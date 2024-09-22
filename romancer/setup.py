from setuptools import setup, find_packages

setup(
    name='romancer',
    version='0.1.0',
    description='romancer',
    author='Edward Geist',
    author_email='egeist@rand.org',
    packages=find_packages(),
    install_requires=[
        'matplotlib',
        'cartopy',
        'shapely',
        'dill',
        'numpy',
        'scipy',
        'pathlib',
        'setuptools',
        'pytest'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3'
    ],
)
