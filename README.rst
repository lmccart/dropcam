Unofficial Python API for Dropcam cameras.

Please note that this API could break if Dropcam updates their service.

Usage
-----

Basic usage ::

    >>> from dropcam import Dropcam
    >>> d = Dropcam(os.getenv("DROPCAM_USERNAME"), 
                    os.getenv("DROPCAM_PASSWORD"))
    >>> for i, cam in enumerate(d.cameras()):
    ...     cam.save_image("camera.%d.jpg" % i)

Installation
------------

  $ git clone https://github.com/lmccart/dropcam.git
  $ cd dropcam
  $ python setup.py install
  $ export DROPCAM_USERNAME=XXX
  $ export DROPCAM_PASSWORD=XXX
  $ #place watching clips in watching/ dir
  $ python dropcam.py #run