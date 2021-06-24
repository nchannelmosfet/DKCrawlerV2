import setuptools


setuptools.setup(
    name="DKCrawlerV2",
    version="0.0.1",
    author="Jerry Wu",
    author_email="nchannelmosfet@gmail.com",
    description="Async Crawler built with PlayWright",
    url="https://github.com/nchannelmosfet/DKCrawlerV2",
    packages=setuptools.find_packages(),
    install_requires=[
        'playwright',
        'pandas',
        'scrapy',
        'ipywidgets',
        'openpyxl',
        'xlrd',
        'ipyfilechooser'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)