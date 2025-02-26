************
Introduction
************

Welcome to the new and improved home of the documentation for the ChipWhisperer software,
following the release of ChipWhisperer 6.0.0. Previously, documentation was
spread across different sites; now everything is right here on one site. We hope this
will make our documentation easier to navigate, and answers to your
questions easier to find.

If you're new to ChipWhisperer, or haven't been following the project recently,
you may want to check out this :ref:`overview <getting_started>` to learn a little
about the project and its recent changes.

The :ref:`installing <install>` sections have everything you need to know to
install ChipWhisperer.

.. _hardware: https://rtfm.newae.com

After setting up your `hardware`_, run:

.. code:: python

    >>> import chipwhisperer as cw
    >>> scope = cw.scope()
    >>> scope
    cwlite Device
    gain =
        mode = low
        gain = 0
        db   = -6.5
    adc =
        state      = False
        basic_mode = low
        timeout    = 2
        offset     = 0
    ...


You now have access to an object-oriented interface to configure the attached
hardware. To see what is possible with this interface check out the
:ref:`scope section <api-scope>` of the API documentation.

If you're not sure what to do next, the :ref:`starting <starting>` section
will point you in the right direction.

Be sure to explore the other sections in the left-side index to learn
everything you can do with ChipWhisperer.

