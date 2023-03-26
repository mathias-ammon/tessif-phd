.. _Installation:

************
Installation
************

Following Sections provide overview on how to install Tessif-phd.

.. contents:: Contents
   :backlinks: top
   :local:

Standard
********

Linux
=====

1. Make sure to have **python3**, **graphviz** and **coinor-cbc** installed on your system. Use your software management of choice to install them. Most Linux distributions have them in their repository.
2. Create a new directory and change to it:

   .. code:: shell

      mkdir /path/to/dir
      cd /path/to/dir

3. Clone the git repository for **tessif-phd** 

   .. code:: shell

      git clone https://collaborating.tuhh.de/ietma/tessif-phd/
    
5. Create a new virtual environment and activate it:

   .. code:: shell
    
      python3 -m venv your_env_name
      source your_env_name/bin/activate
    
6. Make sure **pip**, **setuptools** and **wheel** are up to date:

   .. code:: shell

      pip install -U pip setuptools wheel


7. Install **tessif-phd** and it's requirements:

   .. code:: shell

      pip install tessif-phd/


8. After installation is done you can check if everything went according to plan by executing
   tessif's tests. Do so by entering:

.. code:: shell

   tessif --test_install
       
    
Windows
=======

Windows installation tutorial goes here


Development
***********

Linux
=====

1. Make sure to have **python3**, **graphviz** and **coinor-cbc** installed on your system. Use your software management of choice to install them. Most Linux distributions have them in their repository.
2. Create a new directory and change to it:

   .. code:: shell

      mkdir /path/to/dir
      cd /path/to/dir

3. Clone the git repository for **tessif-phd** 

   .. code:: shell

      git clone https://collaborating.tuhh.de/ietma/tessif-phd/
    
4. Create a new virtual environment and activate it:

   .. code:: shell
    
      python3 -m venv your_env_name
      source your_env_name/bin/activate
    
5. Make sure **pip**, **setuptools** and **wheel** are up to date:

   .. code:: shell

      pip install -U pip setuptools wheel


6. Install **tessif-phd** and it's requirements:

   .. code:: shell
          
      pip install -e tessif-phd/[dev]

7. Currently there is a minor version conflict. After installation, update dash
   and ignore the error, since tessif-phd is not plotting via calliope:

   .. code:: shell

      pip install -U dash
      
8. After installation is done you can check if everything went according to plan by executing
   tessif's tests. Do so by entering:

   .. code:: shell

      tessif --test_install

9. (Optional) Build your own (html) documentation using Sphinx:

   .. code:: shell

      cd tessif-phd/docs/
      make html

   If the build was succesfull you can browse the documentation using your favorite browser
   by opening

   .. code:: shell

      tessif-phd/docs/build/html/index.html


   .. note::
      Sphinx supports a variety of different `builders
      <https://www.sphinx-doc.org/en/master/man/sphinx-build.html>`_ such as Latex or ePub.
   
   
Windows
=======

1. Install all **prerequisites**:
   
   a) Install `python <https://www.python.org/downloads/>`_
      (Use 3.8.x for as there are no scipy wheels for 3.9 right now).

   b) Download CBC (`64 <https://ampl.com/dl/open/cbc/cbc-win64.zip>`_
      or `32 <https://ampl.com/dl/open/cbc/cbc-win32.zip>`_ bit)

   c) Install `glpk <http://www.osemosys.org/uploads/1/8/5/0/18504136/glpk_installation_guide_for_windows10_-_201702.pdf>`_

      (add both the cbc binary and the glpk binary to PATH as described in the guide for glpk)

   d) Install `git <https://git-scm.com/download/win>`_

   e) Install/Open `PowerShell Core
      <https://github.com/powershell/powershell#get-powershell>`_

   f) Install `graphviz <https://graphviz.org/>`_:
      (See `this guide
      <https://forum.graphviz.org/t/new-simplified-installation-procedure-on-windows/224>`_)

      1. `Download <https://www2.graphviz.org/Packages/stable/windows/10/cmake/Release/x64/>`_
	 graphviz for Windows.

      2. Run the installer. Make sure to select one of the options to add graphviz to PATH.

      3. Open the command prompt as administrator:

	 a) Press the Windows-Key
	 b) Type cmd
	 c) Click ``Run as administrator``

      4. Type ``dot -c`` and press Enter

      5. If no warning message is returned, the installation was successfull.

   g) Install `Libxml2 <http://xmlsoft.org/>`_ (See `this guide
      <https://pages.lip6.fr/Jean-Francois.Perrot/XML-Int/Session1/WinLibxml.html>`__
      )

      1. `Download Libxml2 <http://xmlsoft.org/sources/win32/64bit/>`__

      2. Create a new folder (if you wish to make it available for all users
         something like ``C:\Program Files\Libxml2`` works)

      5. `Add Libxml2 to the PATH Variable
         <https://helpdeskgeek.com/windows-10/add-windows-path-environment-variable/>`_

         a) Go to ``Control Panel\All Control Panel Items\System/Advanced system settings``
            ``(Systemsteuerung\System und Sicherheit\System\Erweiterete Systemeinstellung)``
            .
         
	 b) On the tab ``Advanced (Erweitert)`` select ``Environment Variables
            (Umgebungsvariablen)``.

         c) Click on ``System variables (Systemvariablen)`` and add the desired path

   h) Install the `Microsoft Build Tools for C++
      <https://visualstudio.microsoft.com/de/visual-cpp-build-tools/>`_


2. Open `PowerShell (Core)
   <https://github.com/powershell/powershell#-powershell>`_
   as Administrator and create a new directory and change to it:

   .. code:: powershell

      mkdir \path\to\dir
      cd \path\to\dir

3. Clone the git repository for **tessif-phd** 

   .. code:: shell

      git clone https://collaborating.tuhh.de/ietma/tessif-phd/
    
5. Create a new virtual environment and activate it:

   a) If you only have python 3.x.x installed:
      
      .. code:: powershell
    
         python -m venv your_env_name
         \path\to\env\Scripts\activate
         
   b) If you have multiple versions of python installed
      
      (where 3.x would mean 3.8 at this point in time (2023-03-)):
      
      .. code:: powershell
    
         py -3.x.x  -m venv \path\to\env\
         \path\to\env\Scripts\activate         

6. Update `pip <https://pypi.org/project/pip/>`_

   (with your activated virtual environment):
   
   .. code:: powershell

      python -m pip install --upgrade pip
     
7. Make sure `setuptools <https://pypi.org/project/setuptools/>`_ and
   `wheel <https://pypi.org/project/wheel/>`_ are up to date:

   .. code:: powershell

      pip install -U setuptools wheel

8. Install `PyGraphviz <https://pygraphviz.github.io/index.html>`_

   a) `Download <https://www.lfd.uci.edu/~gohlke/pythonlibs/#pygraphviz>`__ the
      latest pygraphvix win .whl (For example
      ``pygraphviz‑1.6‑cp38‑cp38‑win_amd64.whl``) Make sure that the number behind
      ``cp`` matches your python version. i.e cp38 for python 3.8.x

   b) Install the scipy wheel using pip:

      .. code:: powershell

         pip install path\to\whl such as 'Downloads\pygraphviz‑1.6‑cp38‑cp38‑win_amd64.whl'


9. Install **tessif-phd** and it's requirements:

   a) Change into the tessif-phd top folder (somhow on windows this is necessary)

      .. code:: powershell
          
         cd tessif-phd

   b) Install tessif-phd in development mode:
     
      .. code:: powershell
          
         pip install -e ./[dev]


   c) Currently there is a minor version conflict.  After installation, update
      dash and ignore the warning, since tessif is not plotting via Calliope:

      .. code:: shell

	 pip install -U dash

10. After installation is done you can check if everything went according to plan by executing
    tessif's tests. Do so by entering (assuming you're still inside of where you cloned tessif-phd to):

   .. code:: powershell

      python tests/nose_testing.py

11. (Optional) Build your own (html) documentation using Sphinx:

   .. code:: powershell

      cd tessif-phd/docs/
      .\make html

   If the build was succesfull you can browse the documentation using your favorite browser
   by opening

   .. code:: powershell

      tessif-phd/docs/build/html/index.html


   .. note::
      Sphinx supports a variety of different `builders
      <https://www.sphinx-doc.org/en/master/man/sphinx-build.html>`_ such as Latex or ePub.
