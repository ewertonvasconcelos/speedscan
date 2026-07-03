from setuptools import setup
setup(name='speedscan', version='1.0', py_modules=['core'], entry_points={'gui_scripts': {'speedscan=core.main:main'}})
