import lifesospy.const as lifesospy_const
import os

from setuptools import setup


def readme():
    with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
        return f.read()


setup(
    name=lifesospy_const.PROJECT_NAME,
    version=lifesospy_const.PROJECT_VERSION,
    description=lifesospy_const.PROJECT_DESCRIPTION,
    long_description=readme(),
    packages=['lifesospy'],
    install_requires=['aenum'],
    python_requires='>=3.5.3',
    author='Richard Orr',
    url='https://github.com/rorr73/lifesospy',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Home Automation',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
