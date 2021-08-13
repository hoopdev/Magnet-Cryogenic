import setuptools

setuptools.setup(
    name="magnet_cryogenic",
    version='0.1',
    description='Interface for Cryogenic Limited superconducting magnet power supplies',
    author='Kotaro Taga',
    author_email='taga@issp.u-tokyo.ac.jp',
    url='https://github.com/hoopdev/Magnet-Cryogenic',
    license="MIT",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 1 - Planning"
    ],
    install_requires=[
    ],
    python_requires='>=3.7',
)
