========================================
Kihara Lab plugin
========================================
This is a **Scipion** plugin that offers different `Kihara Lab tools <https://kiharalab.org/>`_.
These tools will make it possible to carry out different functions for working with electron density maps.
The code involving these functionalities can be found at https://github.com/kiharalab.

Therefore, this plugin allows to use programs from the DAQ software suite
within the Scipion framework.

========================================
Install this plugin
========================================
You will need to use `Scipion3 <https://scipion-em.github.io/docs/docs/scipion
-modes/how-to-install.html>`_ to run these protocols.

DAQ, Emap2sec, Emap2sec+, and MainMast are installed automatically by scipion.

**Note:** Emap2sec+ needs an Nvidia GPU to run.

- **Install the stable version**

    Through the plugin manager GUI by launching Scipion and following **Others** >> **Plugin Manager**

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

========================================
Protocols
========================================
scipion-em-kiharalab contains the following protocols:

- **DAQ model validation**: Executes the DAQ software to validate a structure model.
- **Emap2sec**: Identifies protein secondary structures.
- **Segment map**: Performs the segmentation of maps into different regions by symmetry using MainMast software.

========================================
Packages & enviroments
========================================
Packages installed by this plugin can be located in ``/path/to/scipion/software/em/``.

The following packages will be created:

- daq-``version``
- emap2sec-``version``
- mainMast-``version``

Where ``version`` is the current version of that specific package.

Also, the following conda enviroments will be created:

- daq-``version``
- emap2sec-``version``
- emap2secPlus-``version``

As of today, Scipion does not automatically uninstall the conda enviroments created in the installation process when uninstalling a plugin, so keep this list in mind if you want to clean up some disk space if you need to uninstall this one.

========================================
External software
========================================
This plugin integrates the following software:
  
.. _daq: https://github.com/kiharalab/DAQ
.. |daq| replace:: **DAQ model validation**
.. _emap2sec: https://github.com/kiharalab/Emap2sec
.. |emap2sec| replace:: **Emap2sec** 
.. _emap2secPlus: https://github.com/kiharalab/Emap2secPlus
.. |emap2secPlus| replace:: **Emap2sec+** 
.. _mainMast: https://github.com/kiharalab/MAINMASTseg
.. |mainMast| replace:: **MainMast** 

- |daq|_: Residue-Wise Local Quality Estimation for Protein Models from Cryo-EM Maps.
- |emap2sec|_: Identifies protein secondary structures.
- |emap2secPlus|_: Detects Protein and DNA/RNA Structures in Cryo-EM Maps of Intermediate Resolution Using Deep Learning.
- |mainMast|_: Automated Segmentation Program for EM map with symmetry.

========================================
Changelog
========================================
All the recent version changes can be found `here <https://github.com/scipion-em/scipion-em-kiharalab/blob/devel/CHANGES.rst>`_.
