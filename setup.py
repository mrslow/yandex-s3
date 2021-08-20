from pathlib import Path

from setuptools import setup, find_packages


description = 'Asyncio compatible SDK for Yandex Object Storage'
long_description = Path('./README.md').resolve().read_text()


ext_modules = None

setup(
    name='yandex-s3',
    version='0.1.1',
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    author='Anton Shchetikhin',
    author_email='animal2k@gmail.com',
    url='https://github.com/mrslow/yandex-s3',
    license='MIT',
    license_file='LICENSE',
    packages=find_packages(),
    python_requires='>=3.8',
    zip_safe=False,
    install_requires=[
        'aiofiles>=0.5.0',
        'cryptography>=3.1.1',
        'httpx>=0.15.5',
        'pydantic>=1.6.1',
    ],
)
