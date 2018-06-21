import lifesospy.const as lifesospy_const

from setuptools import setup

setup(
    name=lifesospy_const.PROJECT_NAME,
    description=lifesospy_const.PROJECT_DESCRIPTION,
    version=lifesospy_const.PROJECT_VERSION,
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
