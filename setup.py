from setuptools import setup, find_packages

setup(
    name="budgie",
    version="0.1",
    description="Budgie, a budget application for normies",
    packages=find_packages(),
    py_modules=["main"],
    include_package_data=True,
    install_requires=[
        "pyqt6",
    ],
    entry_points={
        "console_scripts": [
            "budgie = main:main",
        ],
    },
)
