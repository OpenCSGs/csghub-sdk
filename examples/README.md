# Examples

We host a wide range of example scripts for use CSGHub SDK to interact with the CSGHub server.

While we strive to present as many use cases as possible. It is expected that they won't work out-of-the-box on your specific problem and that you will be required to change a few lines of code to adapt them to your needs. To help you with that, most of the examples fully expose the preprocessing of the data, allowing you to tweak and edit them as required.

## Important note

**Important**

To make sure you can successfully run the latest versions of the example scripts, you have to **install the library from source**. To do this, execute the following steps in a new virtual environment:

```shell
git clone https://github.com/OpenCSGs/csghub-sdk.git
cd csghub-sdk
pip install .
```

Before running the example script, please set the necessary environment variables as follows.

```shell
export HF_ENDPOINT="https://hub.opencsg.com/hf"
```

You can also adapt the script to your own needs.
