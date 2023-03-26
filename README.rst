Tessif-PHD - Transforming Energy Supply System modell I ng Framework - PhD Version
==================================================================================

.. image:: https://zenodo.org/badge/618724258.svg
   :target: https://zenodo.org/badge/latestdoi/618724258

Disclaimer
----------
Original, heavy-weight, implementation of Tessif which was published for reference and transparency reasons and to enable other researchers to reuse various aspects of its code base.

A much more light-weight, application-oriented implementation can be found at: https://github.com/tZ3ma/tessif.

Purpose
-------
Designed to provide a harmonized data input for the Energy Supply System Modelling and Optimization Software (ESSMOS) tools Calliope, FINE, oemof.solph and PyPSA.

Install
-------

To nstall the tessif-phd version of tessif, python 3.8 is recommend.
After the installation, the package will be available as ``tessif``.

1. Clone the git repository for **tessif-phd** 

   .. code:: shell

      git clone https://github.com/tZ3ma/tessif-phd.git
    
2. Create a new virtual environment and activate it:

   .. code:: shell
    
      python3 -m venv your_env_name
      source your_env_name/bin/activate
    
3. Make sure **pip**, **setuptools** and **wheel** are up to date:

   .. code:: shell

      pip install -U pip setuptools wheel


4. Install **tessif-phd** and it's requirements:

   .. code:: shell

      pip install tessif-phd/


5. After installation is done you can check if everything went according to plan by executing
   tessif's tests. Do so by entering:

.. code:: shell

      python tests/nose_testing.py
      
