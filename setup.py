from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='recondite',
    version='0.2',
    description='Tools for reconciling tidy data with Wikidata.',
    long_description=('Tools for streamlining data reconciliation with '
        'Wikidata, focused on efficiency in gathering data and on streamlining '
        'the task of data matching.'),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Wiki'
        ],
    keywords='wikidata wikimedia wikipedia bodleian reconcile data',
    url='http://github.com/argotechnica/recondite',
    author='argotechnica',
    author_email='corysalveson@gmail.com',
    license='MIT',
    packages=['recondite'],
    install_requires=[
        'requests',
        'pandas',
        'bs4'],
    include_package_data=True,
    zip_safe=False)
