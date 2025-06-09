#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, NewAE Technology Inc
# All rights reserved.
#
# Authors: Jean-Pierre Thibault
#
# Find this and more at newae.com - this file is part of the chipwhisperer
# project, https://github.com/newaetech/chipwhisperer
#
#    This file is part of chipwhisperer.
#
#    chipwhisperer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    chipwhisperer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with chipwhisperer.  If not, see <http://www.gnu.org/licenses/>.
#=================================================
from ....common.utils import util
from .. import _OpenADCInterface as OAI

from ....logging import *
import time
import datetime

CODE_READ = 0x80
CODE_WRITE = 0xC0


class OneWireHelper(util.DisableNewAttr):
    ''' Helper functions for bit-banging 1-wire interface.
    Basic functions for sending a reset/pulse detect, as well as arbitrary reads and writes.
    Meant to be overloaded for your particular target. For example, if the command for reading your target's 
    ROM code is 0x33, and its family code is 0x45, you could do::

        class My1wireTarget(cw.capture.scopes.cwhardware.ChipWhispererHuskyBitBanger.OneWireHelper):
            def __init__(self, bitbanger):
                super().__init__(bitbanger)
            def read_rom_code(self, verbose=False):
                return super().read_rom_code(0x33, expected_family_code=0x45, verbose=verbose)
            # ... other useful higher-level functions as needed ...

        target = My1wireTarget(scope.bitbanger)
        target.send_rst_pd()
        target.read_rom_code()
                    
    '''
    _name = '1-wire helper functions'

    def __init__(self, bb):
        super().__init__()
        self.bb = bb
        self.disable_newattr()

    @staticmethod
    def get_rst_pd(rst=56, wait=6, check=2):
        total = rst + wait + check
        if total % 8:
            pad = 8 - total%8
        else:
            pad = 0
        cmdbits = [0]*(rst+wait+check+pad)
        hizbits = [0]*rst
        hizbits.extend([1]*(wait+check+pad))
        penbits = [1]*rst
        penbits.extend([0]*wait)
        penbits.extend([1]*check)
        penbits.extend([0]*pad)
        renbits = [0]*(rst+wait+check+pad)
        return cmdbits, hizbits, penbits, renbits

    def send_rst_pd(self, rst=56, wait=6, check=2, trigger_en=True):
        """ Sends a reset and checks for the target's pulse detect response.

        Args:
            rst (int): number of timeslots for the low reset pulse.
            wait (int): after the reset pulse, number of timeslots to wait before checking for the target's response.
            check (int): number of timeslots that the target's response is checked.
            trigger_en (bool): whether a trigger should be issued at the end of the command.

        """
        self.sendpacket(self.get_rst_pd(rst=rst, wait=wait, check=check), trigger_en=trigger_en)
        assert self.bb.matched, 'no presence detect'

    def sendpacket(self, packet, trigger_en=True, trigger_bit=None, clear_matched=True, timeout=1):
        """ Sends a generic "packet"; waits for it to be sent.

        Args:
            packet (list): list of lists defining the packet, as returned by :class:`get_rst_pd` or :class:`get_generic_write_read`.
            trigger_en (bool): whether a trigger *can be* issued by the bit-banging module. Affected by :class:`BitBanger.trigger_when_matched`
            trigger_bit (int): timeslot on which to issue the trigger; if None, the packet's last timeslot is used.
            clear_matched (bool): setting for :class:`BitBanger.clear_matched`
            timeout (int): if the packet is not done being sent after this many seconds, times out.

        """
        CMD = packet[0]
        HIZ = packet[1]
        PEN = packet[2]
        REN = packet[3]
        assert len(CMD) <= self.bb.max_length, 'Packet too long! Break up the data you are transmitting via sendpacket() into smaller chunks.'

        self.bb.pattern_data = CMD
        self.bb.pattern_hiz = HIZ
        self.bb.pattern_en = PEN
        self.bb.record_en = REN
        self.bb.clk_en = [0]*len(CMD)
        self.bb.num_bits = len(CMD)
        
        self.bb.trigger_en = trigger_en
        self.bb.clear_matched = clear_matched
        TRG = [0]*len(CMD)
        if trigger_bit is None:
            TRG[-1] = 1
        else:
            TRG[trigger_bit] = 1
            
        self.bb.trig_bits = TRG
        self.bb.go()
        self.bb.wait_for_done(timeout)

    @staticmethod
    def crc8(data):
        """ Calculates the 8-bit CRC used in the ROM ID.
        """
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x01:
                    crc = (crc >> 1) ^ 0x8C
                else:
                    crc >>= 1
                crc &= 0xFF
        return crc

    def read_rom_code(self, read_rom_command, expected_family_code=None, verbose=False):
        """ Read the target's ROM code.

        Args:
            read_rom_command (int): target's "read ROM" command
            expected_family_code (optional, int): if provided, an error will be raised if a different family code is read
            verbose (bool): set verbose mode

        """

        self.send_rst_pd(trigger_en=False)
        self.sendpacket(OneWireHelper._get_read_rom(read_rom_command))
        romcode = OneWireHelper._check_read_rom(self.bb.recorded_data(), expected_family_code, verbose)
        return hex(romcode)


    @staticmethod
    def get_generic_write_read(wbytes, rbytes, w1slot=1, w0slot=6, tslot=7, gap=0):
        """Get parameters for sending a desired generic 1-wire write and/or read transaction.
        Use this to build the read/write commands that you'll commonly use.

        Args:
            wbytes (list of ints): Bytes to write. Can be an empty list for a read-only request.
            rbytes (int): Number of bytes to read. Can be 0 for a write-only request.
            w1slot (int): Number of timeslots that line is driven low when sending a "1" bit.
            w0slot (int): Number of timeslots that line is driven low when sending a "0" bit.
            tslot (int): Total number of timeslots per bit.
            gap (int): number of idle timeslots between each byte

        Returns:
            Lists of bits that can be fed to :class:`sendpacket`.
        """

        cmdbits = []
        hizbits = []
        renbits = []
        # writes:
        for cmd in wbytes:
            for i in range(8):
                if cmd & 2**i:
                    # write 1
                    cmdbits.extend([0]*tslot)
                    hizbits.extend([0]*w1slot)
                    hizbits.extend([1]*(tslot-w1slot))
                    renbits.extend([0]*tslot)
                else:
                    # write 0
                    cmdbits.extend([0]*tslot)
                    hizbits.extend([0]*w0slot)
                    hizbits.extend([1]*(tslot-w0slot))
                    renbits.extend([0]*tslot)
            if gap:
                cmdbits.extend([0]*gap)
                hizbits.extend([1]*gap)
                renbits.extend([0]*gap)

        # reads:
        for i in range(8*rbytes):
            cmdbits.extend([0]*tslot)
            hizbits.extend([0])
            hizbits.extend([1]*(tslot-1))
            renbits.extend([0]*2)
            renbits.extend([1])
            renbits.extend([0]*(tslot-3))
            if gap and (i%8 == 0):
                cmdbits.extend([0]*gap)
                hizbits.extend([1]*gap)
                renbits.extend([0]*gap)

        penbits = [1]*len(cmdbits)
        return cmdbits, hizbits, penbits, renbits


    @staticmethod
    def _get_read_rom(read_rom_command, w1slot=1, w0slot=6, tslot=7):
        return OneWireHelper.get_generic_write_read([read_rom_command], 8, w1slot, w0slot, tslot)


    @staticmethod
    def _check_read_rom(raw, expected_family_code, verbose=True):
        family_code = raw & 0xff
        if expected_family_code and (family_code != expected_family_code):
            raise ValueError('Expected family code: %x; got %x' % (expected_family_code, family_code))
        else:
            if verbose: print('Correct family code: %x' % family_code)
        romcode = (raw >> 8) & 2**48-1
        if verbose: print('ROM code: 0x%x' % romcode)
        crc = (raw >> 56) & 0xff
        calc_crc =  OneWireHelper.crc8(list(int.to_bytes(raw & 2**48-1, length=7, byteorder='little')))
        if calc_crc != crc:
            raise ValueError('Incorrect CRC! Expected 0x%x, got 0x%x' % (calc_crc, crc))
        else:
            if verbose: print('Correct CRC: 0x%x' % crc)
        return romcode



class BitBanger (util.DisableNewAttr):
    ''' Husky bit-banger settings. More than just bit-banging: precisely timed bit-banging
    with the ability to trigger at a precise time. This is the lowest-level access class, allowing
    easy control of exactly what you what sent on the wire.

    Example::

        scope.bitbanger.continuous_clk = False
        scope.bitbanger.inactive_data = 0
        scope.bitbanger.inactive_state = 'high_z'
        scope.bitbanger.drive_edge = 'rising'
        scope.bitbanger.check_edge = 'falling'
        scope.bitbanger.trigger_en = True
        scope.bitbanger.clk_div = 4
        scope.bitbanger.num_bits = 5

        scope.bitbanger.pattern_data = [0, 1, 0, 1, 0]
        scope.bitbanger.trig_bits    = [0, 0, 0, 1, 0]
        scope.bitbanger.clk_en       = [1, 1, 0, 1, 1]

        scope.bitbanger.go()

        # this drives the following:

                   ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ ┏─┐ 
        clock in : ┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─┛ └─
                   ____╱              ╲╱              ╲╱              ╲╱              ╲╱              ╲____
        bit count:     ╲    bit 0     ╱╲    bit 1     ╱╲    bit 2     ╱╲    bit 3     ╱╲    bit 4     ╱    
                       ┌───────┐       ┌───────┐                       ┌───────┐       ┌───────┐           
        clock out: ────┘       └───────┘       └───────────────────────┘       └───────┘       └───────────
                   ____┐               ┌───────────────┐               ┌───────────────┐               ____
        data out :     └───────────────┘               └───────────────┘               └───────────────    
                                                                               ┌───────────────┐           
        trigger  : ────────────────────────────────────────────────────────────┘               └───────────


    (timing diagram generated by asciiwave: https://github.com/Wren6991/asciiwave)
    '''
    _name = 'Husky Bit-Banger Settings'

    def __init__(self, oaiface : OAI.OpenADCInterface):
        # oaiface = OpenADCInterface
        super().__init__()
        self.oa = oaiface
        self._trigger_en = 0
        self._clear_matched = 0
        self._continuous_clk = 0
        self._inactive_data = 0
        self._inactive_state = 'high_z'
        self._trigger_when_matched = 0
        self._enable_glitch_output = 0
        self._drive_edge = 'rising'
        self._check_edge = 'falling'
        self._clk_div = 0
        self._num_bits = 0
        self.max_length = self._read_max_pattern()
        self._pattern_data = [0]*self.max_length
        self._pattern_en = [1]*self.max_length
        self._pattern_hiz = [0]*self.max_length
        self._record_en = [0]*self.max_length
        self._trig_bits = [0]*self.max_length
        self._clk_en = [1]*self.max_length
        self.onewire = OneWireHelper(self)
        self.disable_newattr()

    def _dict_repr(self):
        rtn = {}
        rtn['max_length'] = self.max_length
        rtn['clk_div'] = self.clk_div
        rtn['drive_edge'] = self.drive_edge
        rtn['check_edge'] = self.check_edge
        rtn['inactive_state'] = self.inactive_state
        rtn['inactive_data'] = self.inactive_data
        rtn['continuous_clk'] = self.continuous_clk
        rtn['num_bits'] = self.num_bits
        return rtn

    def __repr__(self):
        return util.dict_to_str(self._dict_repr())

    def __str__(self):
        return self.__repr__()

    def _read_max_pattern(self):
        raw = self.oa.sendMessage(CODE_READ, "BB_TRIG_CTRL_STAT", maxResp=3)
        return raw[1] + (raw[2] << 8)

    @property 
    def matched(self):
        """ Whether the pattern specified by :class:`pattern_data`, along with :class:`pattern_en`,
        was seen to "match". Useful when the data line is bidirectional.
        """
        raw = self.oa.sendMessage(CODE_READ, "BB_TRIG_CTRL_STAT", maxResp=1)[0]
        if raw & 0x01:
            return True
        else:
            return False

    @property 
    def active(self):
        """ Whether the bitbanger module is still currently active (i.e. still bit-banging).
        """
        raw = self.oa.sendMessage(CODE_READ, "BB_TRIG_CTRL_STAT", maxResp=1)[0]
        if raw & 0x02:
            return True
        else:
            return False

    def go(self, go=True):
        """ Make the bitbanger go.
        """
        # Most properties of this module are only written out to the hardware when this
        # method is called; by setting the "go" argument to False, the properties get
        # pushed out without making it "go".
        if go:
            writes = 6
        else:
            writes = 5
        raw = [0]*writes
        if self.drive_edge == 'rising':
            drive = 1
        else:
            drive = 0
        if self.check_edge == 'rising':
            check = 1
        else:
            check = 0
        if self.inactive_state == 'driven':
            inactive_state = 1
        else:
            inactive_state = 0

        raw[0] = (self.trigger_en << 7) + \
                 (self.clear_matched << 6)
        raw[1] = (self.continuous_clk << 7) + \
                 (self.inactive_data << 6) + \
                 (inactive_state << 5) + \
                 (self.trigger_when_matched << 3) + \
                 (self.enable_glitch_output << 2) + \
                 (drive << 1) + \
                 (check << 1)
        raw[2] = self.clk_div
        raw[3] = self.num_bits & 0xFF
        raw[4] = self.num_bits >> 8
        self.oa.sendMessage(CODE_WRITE, "BB_TRIG_CTRL_STAT", raw)

    def wait_for_matched(self, timeout=1):
        """ Polls :class:`matched` until timeout.

        Args:
            timeout (int): number of seconds for timeout.

        """
        starttime = datetime.datetime.now()
        while (datetime.datetime.now() - starttime).total_seconds() < timeout:
            matched = self.matched
            running = self.active
            if matched:
                return True
            elif not running and not matched:
                return False
        raise ValueError('Timed out!')

    def wait_for_done(self, timeout=1):
        """ Polls :class:`active` until timeout.

        Args:
            timeout (int): number of seconds for timeout.

        """
        starttime = datetime.datetime.now()
        while (datetime.datetime.now() - starttime).total_seconds() < timeout:
            if not self.active:
                return
        raise ValueError('Timed out!')


    @property 
    def trigger_en(self):
        """ Specify whether a trigger can be generated.
        Note that other properties determine whether (and when) a trigger is issued:
        :class:`trig_bits` and :class:`trigger_when_matched`.
        """
        return self._trigger_en
    @trigger_en.setter
    def trigger_en(self, val):
        if val not in [0, 1]:
            raise ValueError()
        self._trigger_en = val

    @property 
    def clear_matched(self):
        """ TODO: not sure this is needed?
        """
        return self._clear_matched
    @clear_matched.setter
    def clear_matched(self, val):
        if val not in [0, 1]:
            raise ValueError()
        self._clear_matched = val

    @property 
    def continuous_clk(self):
        """ Specify whether the clock should run continuously.
        If False, the clock is generated only while the bitbanger is active
        and :class:`clk_en` is set.
        """
        return self._continuous_clk
    @continuous_clk.setter
    def continuous_clk(self, val):
        if val not in [0,1]:
            raise ValueError
        self._continuous_clk = val
        self.go(False)

    @property 
    def inactive_data(self):
        """ Specify the state of the data line when this module is inactive.

        Args:
            val (int): 0 or 1.

        """
        return self._inactive_data
    @inactive_data.setter
    def inactive_data(self, val):
        if val not in [0,1]:
            raise ValueError
        self._inactive_data = val
        self.go(False)

    @property 
    def inactive_state(self):
        """ Specify whether the data line is driven when this module is inactive.

        Args:
            val (str): 'driven' or 'high_z'.

        """
        return self._inactive_state
    @inactive_state.setter
    def inactive_state(self, val):
        if val not in ['driven', 'high_z']:
            raise ValueError
        self._inactive_state = val
        self.go(False)

    @property 
    def trigger_when_matched(self):
        """ Specify whether the observed data needs to match :class:`pattern_data`
        (and :class:`pattern_en`) in order for a trigger to be generated.
        """
        return self._trigger_when_matched
    @trigger_when_matched.setter
    def trigger_when_matched(self, val):
        if val not in [0,1]:
            raise ValueError
        self._trigger_when_matched = val

    @property 
    def enable_glitch_output(self):
        """ TODO - unsure if this will live here?
        """
        return self._enable_glitch_output
    @enable_glitch_output.setter
    def enable_glitch_output(self, val):
        if val not in [0,1]:
            raise ValueError
        self._enable_glitch_output = val

    @property 
    def drive_edge(self):
        """ Selects which clock edge of the generated clock is used to drive out data.

        Args:
            edge (str): 'rising' or 'falling'.

        """
        return self._drive_edge
    @drive_edge.setter
    def drive_edge(self, edge):
        if edge not in ['rising', 'falling']:
            raise ValueError
        self._drive_edge = edge

    @property 
    def check_edge(self):
        """ Selects which clock edge of the generated clock is used to trigger, record data, and check
        expected pattern data.
        When set to the same value as :class:`drive_edge`, data is driven and sampled on the same edge.
        When set to the alternate value, checking is always done half a clock period *after* driving.

        Args:
            edge (str): 'rising' or 'falling'.

        """

        return self._check_edge
    @check_edge.setter
    def check_edge(self, edge):
        if edge not in ['rising', 'falling']:
            raise ValueError
        self._check_edge = edge


    @property 
    def clk_div(self):
        """ Specify the clock divider for the generated clock and for defining the length of
        the time slots for :class:`pattern_data` and its associated properties. Must be even.

        Args:
            val (int): clock divider. Must be even and < 256.

        """
        return self._clk_div
    @clk_div.setter
    def clk_div(self, val):
        if val not in range(2, 256, 2):
            raise ValueError
        self._clk_div = val
        self.go(False)

    @property 
    def num_bits(self):
        """ Specify the number of bits to send when :class:`go()` is issued.
        """
        return self._num_bits
    @num_bits.setter
    def num_bits(self, val):
        if val not in range(1, self.max_length):
            raise ValueError
        self._num_bits = val

    @property
    def pattern_data(self):
        """ Bit-bang data. 
        In the case of a bi-directional data line, this can serve a second purpose: when
        the corresponding bit in :class:`pattern_en` is True, data on the line is compared
        against the `pattern_data` value. This can be used to control whether a trigger is
        generated or not (via :class:`trigger_when_matched`), or simply to know whether the
        expected data was seen (via :class:`matched`).

        Args:
            val (list): list of binary values.

        """
        return self._pattern_data
    @pattern_data.setter
    def pattern_data(self, val):
        self._pattern_data = val
        self._data_setter(val, 'BB_TRIG_PATTERN_DATA')

    @property
    def pattern_en(self):
        """ Bit-bang pattern enable.
        See :class:`pattern_data` for its application.

        Args:
            val (list): list of binary values.

        """
        return self._pattern_en
    @pattern_en.setter
    def pattern_en(self, val):
        self._pattern_en = val
        self._data_setter(val, 'BB_TRIG_PATTERN_EN')

    @property
    def pattern_hiz(self):
        """ Bit-bang pattern high-z.
        Intended for a bi-directional data line: control when the line is driven and when it is not.

        Args:
            val (list): list of binary values.

        """
        return self._pattern_hiz
    @pattern_hiz.setter
    def pattern_hiz(self, val):
        self._pattern_hiz = val
        self._data_setter(val, 'BB_TRIG_PATTERN_HIZ')

    @property
    def record_en(self):
        """ Record enable.
        Intended for a bi-directional data line: control when the line is driven and when it is not.

        Args:
            val (list): list of binary values.

        """
        return self._record_en
    @record_en.setter
    def record_en(self, val):
        self._record_en = val
        self._data_setter(val, 'BB_TRIG_RECORD_EN')

    @property
    def trig_bits(self):
        """ Pattern bits on which to (potentially) issue a trigger.
        Whether or not triggers are issued depends on :class:`trigger_when_matched`.

        Args:
            val (list): list of binary values.

        """
        return self._trig_bits
    @trig_bits.setter
    def trig_bits(self, val):
        self._trig_bits = val
        self._data_setter(val, 'BB_TRIG_BITS')

    @property
    def clk_en(self):
        """ Time slots where the output clock is enabled.
        Ignored when :class:`continuous_clk` is set.

        Args:
            val (list): list of binary values.

        """
        return self._clk_en
    @clk_en.setter
    def clk_en(self, val):
        self._clk_en = val
        self._data_setter(val, 'BB_TRIG_CLK_EN')


    def _data_setter(self, val, reg):
        if len(val) > self.max_length:
            raise ValueError('Too long!')
        raw = self.bytes_from_bits(val)
        self.oa.sendMessage(CODE_WRITE, "BB_TRIG_REG_SELECT", [self.oa.registers[reg]])
        self.oa.sendMessage(CODE_WRITE, "BB_TRIG_DATA", raw)


    def recorded_data(self, nbytes=8, return_word=True):
        """ TODO-doc - including bit/nibble/byte order (may need to add options for those)
        """
        assert nbytes <= 8
        self.oa.sendMessage(CODE_WRITE, "BB_TRIG_REG_SELECT", [self.oa.registers['BB_TRIG_SAVED_DATA']])
        raw = self.oa.sendMessage(CODE_READ, "BB_TRIG_DATA", maxResp=nbytes)
        final = []
        for b in raw:
            # swap nibbles *and* bit order:
            fixed = 0
            for bit in range(8):
                if b & 2**bit:
                    fixed += 2**(7-bit)
            lo = fixed & 0x0F
            hi = fixed & 0xF0
            bswap = (hi >> 4) + (lo << 4)
            final.append(fixed)
        if return_word:
            return int.from_bytes(final, byteorder='big')
        else:
            return final[::-1]

    @staticmethod
    def bytes_from_bits(bits):
        pad = len(bits)%8
        if pad:
            pad = 8 - pad
            pad_value = bits[-1]
            bits.extend([pad_value]*pad)
        sum = 0
        for i,j in enumerate(bits):
            if j: sum += 2**i
        return list(int.to_bytes(sum, len(bits)//8, byteorder='little'))


