.. _install-windows-exe:

####################
Windows Installation
####################

*************************
Windows Bundled Installer
*************************

.. warning:: It is recommended that you enable long paths on Windows
            to prevent any files from not being copied during installation.
            Follow https://www.microfocus.com/documentation/filr/filr-4/filr-desktop/t47bx2ogpfz7.html,
            then reboot to enable long paths

.. _win_prereqs:

========================
Prerequisites
========================

The only prerequisite for ChipWhisperer on Windows is enabling and installing a distribution
for Windows Subsystem for Linux (WSL). If you don't already have this enabled:

1. Follow `Microsoft's instructions for enabling WSL <https://learn.microsoft.com/en-us/windows/wsl/install>`_.
2. Restart your computer.
3. Open a command prompt or powershell windows and run :code:`wsl --install -d ubuntu`

Our Windows installer will install some compilers for building target firmware. This step requires an
internet connection, so if you want to complete this step ahead of time, or if this step fails during
installation, please see :ref:`Installing_Compilers_In_WSL`.

.. _win_run_install:

========================
Running the Installer
========================

If you want to run a native Windows installation of ChipWhisperer, your best 
bet is to run the Windows installer, which takes care of getting the 
prerequisites for you. The steps for using the installer are as follows:

 * Navigate to the `ChipWhisperer release page <https://github.com/newaetech/chipwhisperer/releases>`_ on Github.

 .. image:: _images/win-installer-1.png
    :width: 800

 * Find the latest ChipWhisperer Windows install executable (currently 
   :code:`Chipwhisperer.v6.0.0.exe`)

 * Run the installer. A summary of the installation is given on the second page.

   .. image:: _images/win-installer-2.png
    :width: 800

 * Run the executable and choose the path you want to install ChipWhisperer at. 
   You must have read/write permissions for the location you install to, so 
   avoid installing in a location like :code:`C:\Program Files` or the like. The 
   default install location (the user's home directory) will work for most users.

 * Choose whether or not you want to create a desktop shortcut for running 
   ChipWhisperer.

 * Wait for the installation to finish. Additional windows will pop up during the installation to setup Python and install WSL compilers.

 * Some additional checks are run after the installation has completed. If any issues arise, you will be notified via a message box.

.. _Installing_Compilers_In_WSL:

============================
Installing Compilers In WSL:
============================

ChipWhisperer uses WSL for building target firmware. This part of the install is independent from the
rest of the install process, and can easily be completed before or after running the installer. To install
the target compilers, make sure you have the :ref:`prerequisites installed <_win_prereqs>`, then:

1. Run WSL
2. Run :code:`sudo apt update`.
3. Run :code:`sudo apt install -y build-essential gcc-arm-none-eabi gcc-avr avr-libc`

.. image:: _images/win-installer-3.png
    :width: 800

=====================
Running ChipWhisperer
=====================

Once you've completed the above, you should have a fully functioning, self-contained installation
with everything you need. Since everything is self-contained, or at least as so far is possible on Windows,
you will only have access to ChipWhisperer, the compilers, git bash, when you run our provided applications.

The easiest way to launch ChipWhisperer and get started with the tutorials is by running the ChipWhisperer
application, available via the Start Menu, the folder where you installed ChipWhisperer, or, if you selected
this, via a desktop shortcut. After running, you should see a terminal pop up, followed by a new window open 
in your browser:

.. image:: _images/Jupyter\ ChipWhisperer.png

Once you see this open, we recommend clicking on :code:`jupyter`, then running through :code:`0 - Introduction to Jupyter Notebooks.ipynb`
to verify that everything installed correctly. If you run into any issues, please ask on our `forums`_ for help.

This install bundles Git Bash, which we use to ensure :code:`%%bash` blocks in Jupyter function correctly. If you want
to run this Git Bash with access to ChipWhisperer, the compilers, etc. you can run the ChipWhisperer Bash application,
available from the same spots as the normal ChipWhisperer installation.

.. _releases: https://github.com/newaetech/chipwhisperer/releases

.. _forums: https://forum.newae.com/

.. _manual-windows-install:

**********************
Windows Manual Install
**********************

If you run into issues with the bundled installer, or prefer to grab everything yourself, you can also install ChipWhisperer
manually on Windows. Before grabbing ChipWhisperer itself, you'll need to grab some prerequisites:

========
Git Bash
========

To start off, you'll want to grab `git-bash`_, which we'll use as our general purpose terminal. You can use all default options
during the installation, except for :code:`Enable experimental support for pseudo consoles`, which we recommend enabling,
as it allows the Python interpreter to function correctly on the command line.

======
Python
======

We recommend grabbing Python via `WinPython`_. **Make sure you grab the Cython version, not the PyPy version. Typically, the version with the most downloads/week is the best to grab.**. 
Any Python version above or equal to 3.7 should work here; however, we've only verified installation on Python 3.7, 3.8, 3.9, and 3.10. The default installation instructions will suffice here. Once
WinPython is installed, you'll need to add it to your system path. Don't add it to your user path, as
Git Bash won't be able to pick it up from there.

==================
Compilers and Make
==================

We recommend that you grab both `avr-gcc`_ and `arm-none-eabi-gcc`_. Once you've got them installed
add the :code:`bin\ ` folders from both to your system path.

===================================
Verifying Prerequisite Installation
===================================

Once you've got all the prerequisites installed open Git Bash and run the following to verify
that everything is installed properly and on your system Path:

.. code:: bash

    python -c "import sys; print(sys.executable)" # verify Python installation
    make --version # verify Make from avrgcc
    avr-gcc --version # verify avrgcc
    arm-none-eabi-gcc --version # verify arm-none-eabi-gcc

========================
Installing ChipWhisperer
========================

With all the prerequisites installed and verified, you're ready to install ChipWhisperer
proper.

You can clone and install ChipWhisperer by running the following commands in Git Bash:

.. code:: bash

    cd ~/
    git clone https://github.com/newaetech/chipwhisperer
    cd chipwhisperer
    git submodule update --init jupyter
    python -m pip install -e .
    python -m pip install -r jupyter/requirements.txt

You may also want to grab `nbstripout`_, which will make git and jupyter interact a little nicer:

.. code:: bash

    cd jupyter
    pip install nbstripout
    nbstripout --install # must be run from the jupyter folder

If everything there completes successfully, then congratulations, you've successfully installed ChipWhisperer!
All that's left is to launch Jupyter and run the verification notebooks. Run the following in Git Bash:

.. code:: bash

    cd ~/chipwhisperer
    python -m jupyter notebook

After running, you should see a terminal pop up, followed by a new window open 
in your browser:

.. image:: _images/Jupyter\ ChipWhisperer.png

Once you see this open, we recommend clicking on :code:`jupyter`, then running through :code:`0 - Introduction to Jupyter Notebooks.ipynb`
to verify that everything installed correctly. If you run into any issues, please ask on our `forums`_ for help.


.. _arm-none-eabi-gcc: https://developer.arm.com/open-source/gnu-toolchain/gnu-rm/downloads
.. _avr-gcc: https://blog.zakkemble.net/avr-gcc-builds/
.. _git-bash: https://git-scm.com/downloads
.. _WinPython: https://sourceforge.net/projects/winpython/files/
.. _nbstripout: https://github.com/kynan/nbstripout