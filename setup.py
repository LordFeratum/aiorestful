from setuptools import setup, find_packages


install_reqs = []
with open("requirements.txt") as fp:
    install_reqs = fp.readlines()


setup(
    name="aiorestful",
    version="0.4.0",
    description="Helpers to create a complete aiohttp rest framework",
    author=["Enrique Piña Monserrat"],
    packages=find_packages(),
    install_requires=install_reqs,
    zip_safe=False
)
