from setuptools import setup

setup(
    name='lifesospy',
    version='0.1.0',
    packages=['lifesospy'],
    install_requires=['aenum'],
    description='Provides an interface to LifeSOS alarm systems.',
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
