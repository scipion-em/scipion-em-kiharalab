=======================
Kihara Lab plugin
=======================

This is a **Scipion** plugin that offers different **Kihara Lab tools**.
These tools will make it possible to carry out different functions for working with electron density maps

Therefore, this plugin allows to use programs from the DAQ software suite
within the Scipion framework.

==========================
Install this plugin
==========================

You will need to use `Scipion3 <https://scipion-em.github.io/docs/docs/scipion
-modes/how-to-install.html>`_ to run these protocols.


1. **Install the plugin in Scipion**

DAQ is installed automatically by scipion.

- **Install the stable version (Not available yet)**

    Through the plugin manager GUI by launching Scipion and following **Configuration** >> **Plugins**

    or

.. code-block::

    scipion3 installp -p scipion-em-kiharalab


- **Developer's version**

    1. Download repository:

    .. code-block::

        git clone https://github.com/scipion-em/scipion-em-kiharalab.git

    2. Install:

    .. code-block::

        scipion3 installp -p path_to_scipion-em-kiharalab --devel


