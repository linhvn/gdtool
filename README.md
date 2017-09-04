## Google Drive Tool
With command line interface, multi users function, this tool would make your google drive easier to manage. 
<br /><br />

## Prerequisites

To run this quickstart, you'll need:

- [x] Python 3 or greater.
- [x] The pip3 package management tool.
- [x] Access to the internet and a web browser.
- [x] A Google account with Google Drive enabled.

Please ask google to prepare these tool.


## Installation
Follow these steps to setup google drive API account and python client library

### Step 1: Turn on the Drive API

1. Use this [wizard](https://console.developers.google.com/start/api?id=drive) to create or select a project in the Google Developers Console and automatically turn on the API. Click Continue, then Go to credentials.
2. On the Add credentials to your project page, click the Cancel button.
3. At the top of the page, select the OAuth consent screen tab. Select an Email address, enter a Product name if not already set, and click the Save button.
4. Select the Credentials tab, click the Create credentials button and select OAuth client ID.
5. Select the application type Other, enter the name "Drive API Quickstart", and click the Create button.
6. Click OK to dismiss the resulting dialog.
7. Click the file_download (Download JSON) button to the right of the client ID.

### Step 2: Install the Google Client Library
Run the following command to install the library using pip:
```command
pip3 install --upgrade google-api-python-client
```

## Run the tool
### Usage
General syntax:
```
python gdtool.py [--user=<USER_ID>] <COMMAND> [OPTIONS]
```
`USER_ID` is a sort name for your google account on this tool. It can be whatever do you want (but please do not have space) but it must be unique. If you do not have `[--user=<USER_ID>]`, the default user will be used.
<br />
For example, I have account `_edward.estrada@gmail.com_`, I can use `edw` as a USER ID for this account.
<br /><br />
General help text:
```
positional arguments:
  COMMAND               Command to execute
    adduser             Add an user to Google Drive Tool
    setuser             Set an user as default
    create              Create new folder/directory
    delete              Delete a folder or a file
    list                List of drive files
    clone               Clone a public drive to your drive
    push                Push file to your drive
    pull                Download from Drive to local
    search              Search file in your drive
    reset               Rerset Google Drive Tool configurations

optional arguments:
  -h, --help            show this help message and exit
  -u USER, --user USER  Google user account will be use
```

To get ***COMMAND*** help, use command:
```
python gdtool.py COMMAND --help
```
<br />
### List commands
***adduser***:
```
python gdtool.py adduser -f <OAUTH_JSON_FILE> [-i USER_ID] [-d]
```
- `OAUTH_JSON_FILE` is path to json file, which you downloaded at *step 1*
- `-d` will make this user as default
<br /><br />

***setuser***
```
python gdtool.py setuser <USER_ID>
```
set *_USER_ID_* to default
<br /><br />

***create***
```
python gdtool.py create <NEW_NAME> [-t DIR]
```
create new folder in *DIR* directory. If *DIR* is empty, root folder will be used.
<br /><br />

***delete***
```
python gdtool.py delete <PATH_TO_DELETE>
```
Delete *PATH* in your drive
<br /><br />


***list***
```
python gdtool.py list (-d DIR | -i ID | -l LINK)
```
use one of types:
- `-d DIR` list content of *DIR* in your drive
- `-i ID` list content of an *ID*
- `-l LINK` list content of a *LINK*
<br /><br />

***clone***
```
python gdtool.py clone <LINK> [-t TO_DIR] [-f]
```
this command will force copy resource from *LINK* to *TO_DIR* in your drive or set you as it owner. If *TO_DIR* is empty, the root will be used
- `LINK` the link to clone
- `-t TO_DIR` The folder to save. If this *dir* is not exist, it will be created automaticaly
- `-f` force copy. It will increate your drive size.
<br /><br />


***push***
```
python gdtool.py push <PATH> [-t TO_DIR]
```
this command will push file or folder from *PATH* to *TO_DIR* in your driver. If *TO_DIR* is empty, the root will be used
- `PATH` the path to push
- `-t TO_DIR` The folder to save. If this *dir* is not exist, it will be created automaticaly
<br /><br />



***pull***
```
python gdtool.py pull <PATH> [-t TO_DIR]
```
this command will download file or folder from *PATH* in your driver to *TO_DIR* in your local.
- `PATH` the path to push. This is a your file/folder drive address path. Ex: `/ebooks/english/toeic.pdf`
- `-t TO_DIR` The folder in your local to save.
<br /><br />


***search***
```
gdtool.py search (-s SEARCH_TEXT | -i SEARCH_ID) [-d DIR] [-f | -o | -a] [-p]
```
- `-s` search with text
- `-i` search by drive ID
- `-d` the folder to searching in
- `-f` search with file only
- `-o` search folder only
- `-a` search with both file and folder
- `-p` show parent information only
<br /><br />


***reset***
```
gdtool.py reset
```
This command will reset all configurations. You must _adduser_ again after call this command.
