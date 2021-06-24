import setuptools


setuptools.setup(
    name="scrapy_etl",
    version="0.0.1",
    author="Jerry Wu",
    author_email="jwu@digitalairstrike.com",
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
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
