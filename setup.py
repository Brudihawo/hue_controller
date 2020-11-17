import setuptools

with open("README.md", "r") as file:
    descr_long = file.read()

setuptools.setup(
    name="hue_controller_py",
    version="0.1",
    author="Brudihawo",
    author_email="hawo.hoefer98@freenet.de",
    scripts=["hue_controller/hue_controller.py"],
    description="A Command Line Interface for Controlling Hue Lights",
    long_description=descr_long,
    long_description_content_type="text/markdown",
    url="https://github.com/Brudihawo/hue_controller.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language::Python::3",
        "License::MIT License",
        "Operating System::OS Independent"
    ],
    python_requires=">=3.6")
