import setuptools

with open("README.md", "r") as fh:
        long_description = fh.read()

setuptools.setup(name="example-pkg-your-username", version="0.0.1",
                 author="Filippo Bergamasco", author_email="filippo.bergamasco@unive.it",
                 description="WASS 3D data visualzer",
                 long_description=long_description,
                 long_description_content_type="text/markdown",
                 url="https://github.com/fbergama/wassncplot",
                 packages=setuptools.find_packages(),
                 classifiers=["Programming Language :: Python :: 3", "License :: OSI Approved :: MIT License", "Operating System :: OS Independent", ],)
