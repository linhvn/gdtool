
from __future__ import print_function
import httplib2
import os
import io
import sys
import mimetypes
import json
import urllib.parse

from apiclient import discovery
from apiclient import errors
from apiclient.http import MediaFileUpload
from apiclient.http import MediaIoBaseDownload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

args = None



# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
APPLICATION_NAME = 'Drive API Tool - Python'
APPLICATION_DIR = os.path.join(os.path.expanduser('~'), '.gdtool')
APPLICATION_CREDENTIALS_DIR = os.path.join(APPLICATION_DIR, 'credentials')
APPLICATION_OAUTH_DIR = os.path.join(APPLICATION_DIR, 'oauths')
APPLICATION_CONFIG_FILE = os.path.join(APPLICATION_DIR, 'gdtool.config')
APPLICATION_CONFIGS = {}

JSON_EXTENSION = '.json'
ROOT_FOLDER_ID = 'root'
DOC_MIME_TYPES = ['text/html', 'application/zip', 'text/plain', 'application/rtf', 'application/vnd.oasis.opendocument.text', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/epub+zip', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/x-vnd.oasis.opendocument.spreadsheet', 'text/csv', 'text/tab-separated-values', 'image/jpeg', 'image/png', 'image/svg+xml', 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'application/vnd.oasis.opendocument.presentation', 'application/vnd.google-apps.script+json']

DEFAULT_USER_ID = ''
CURRENT_USER_ID = ''



def get_credentials():
  credential_path = os.path.join(APPLICATION_CREDENTIALS_DIR, 'drive-python-' + CURRENT_USER_ID + '.json')

  store = Storage(credential_path)
  credentials = store.get()
  if not credentials or credentials.invalid:
      flow = client.flow_from_clientsecrets(get_user_infor(CURRENT_USER_ID)['json_file'], SCOPES)
      flow.user_agent = APPLICATION_NAME
      if args:
        credentials = tools.run_flow(flow, store, args)
      else: # Needed only for compatibility with Python 2.6
          credentials = tools.run(flow, store)
      print('Storing credentials to %s' % credential_path)
  return credentials

def http():
  credentials = get_credentials()
  http = credentials.authorize(httplib2.Http())
  return http

def service():
  service = discovery.build('drive', 'v3', http=http())
  return service

def get_user_infor(user_id) :
  if 'users' in APPLICATION_CONFIGS and user_id in APPLICATION_CONFIGS['users'] :
    return APPLICATION_CONFIGS['users'][user_id]

  return {}

def get_app_configs() :
  configs = {}
  if os.path.exists(APPLICATION_CONFIG_FILE) :
    with open(APPLICATION_CONFIG_FILE) as json_data :
      configs = json.load(json_data)

  return configs


##########################
def _search_by_query(search_query) :
  try :
    searching_list = []
    page_token = None
    while True :
      results = service().files().list(pageSize=1000, q=search_query, spaces='drive', fields='nextPageToken, files(kind,id,name,mimeType,ownedByMe,parents)', pageToken=page_token).execute()
      
      searching_list.extend(results.get('files', []))
      page_token = results.get('nextPageToken', None)
      if page_token is None:
        break

    return searching_list
  except errors.HttpError as e:
    print("ERROR on search_file: %s" % str(e))
    return []



def is_folder_exist_in_my_drive(folder_name, parent_id):
  folder_info = get_folder_info(folder_name, parent_id)
  if not folder_info or 'ownedByMe' not in folder_info: 
    return False
  else :
    
    return folder_info['ownedByMe']



def get_folder_info(folder_name, parent_id):
  if folder_name is None or folder_name == "" :
    return []

  search_query = "mimeType='application/vnd.google-apps.folder' and trashed = false and "
  search_query += "name = '%s'" % (urllib.parse.quote_plus(folder_name))
  if(parent_id is not None):
    search_query += " and '%s' in parents" % parent_id
  
  folder_info = _search_by_query(search_query)
  if not folder_info :
    return []

  return folder_info[0]



def is_file_name_in_my_drive(file_name, parent_id):
  file_info = get_file_info_by_name(file_name, parent_id)
  if not file_info or 'ownedByMe' not in file_info :
    return False
  else :
    return file_info['ownedByMe']



def get_file_info_by_name(file_name, parent_id):
  if file_name is None or file_name == "" :
    return []

  search_query = "mimeType != 'application/vnd.google-apps.folder' and trashed = false and "
  search_query += "name = '%s'" % (urllib.parse.quote_plus(file_name))
  if(parent_id is not None):
    search_query += " and '%s' in parents" % parent_id

  file_info = _search_by_query(search_query)
  if not file_info :
    return []

  return file_info[0]




def is_file_exist_on_my_drive(file_id):
  file_info = get_file_info(file_id)
  if file_info == None or 'ownedByMe' not in file_info: 
    return False
  else:
    return file_info['ownedByMe']



def get_file_info(file_id):
  try:
    return service().files().get(fileId=file_id, fields='kind,id,name,mimeType,trashed,parents,spaces,ownedByMe,shared,owners,sharingUser').execute();
  except errors.HttpError as e:
    # print(e.__dict__)
    if e.resp.status != 404 :
      print("ERROR on get_file_info: " + str(e))
    return None



def find_folder(path, parent_id) :
  if(len(path.split("/")) > 1 or len(path.split("\\")) > 1):
    if(len(path.split("/")) > 1):
      list_folder_name = path.split("/")
    if(len(path.split("\\")) > 1):
      list_folder_name = path.split("\\")

    if(is_folder_exist_in_my_drive(list_folder_name[0], parent_id)) :
      root_fid = get_folder_info(list_folder_name[0], parent_id)['id']
      del list_folder_name[0]
      return find_folder('/'.join(list_folder_name), root_fid)
    else :
      return None

  if(is_folder_exist_in_my_drive(path, parent_id)) :
    return get_folder_info(path, parent_id)['id']
  else :
    return None





def get_file_path(file_id, all_folders) :
  file_info = get_file_info(file_id);

  file_path = file_info['name'];
  if 'parents' in file_info and file_info['parents'] is not None :
    file_path = get_file_path(file_info['parents'][0], all_folders) + "/" + file_path
  else :
    file_path = "/" + file_path

  return file_path;




def create_folder(folder_name, parent_id):
  if(len(folder_name.split("/")) > 1 or len(folder_name.split("\\")) > 1):
    if(len(folder_name.split("/")) > 1):
      list_folder_name = folder_name.split("/")
    if(len(folder_name.split("\\")) > 1):
      list_folder_name = folder_name.split("\\")

    root_fid = create_folder(list_folder_name[0], parent_id)
    del list_folder_name[0]
    return create_folder('/'.join(list_folder_name), root_fid)


  if(is_folder_exist_in_my_drive(folder_name, parent_id)):
    return get_folder_info(folder_name, parent_id)['id']

  folder_metadata = {
    'name' : folder_name,
    'mimeType' : 'application/vnd.google-apps.folder'
  }
  if(parent_id is not None):
    folder_metadata['parents'] = [ parent_id ]
  else :
    folder_metadata['parents'] = [ ROOT_FOLDER_ID ]
  folder = service().files().create(body=folder_metadata, fields='id').execute()
  print("created folder " + folder_name)

  return folder['id']




def copy_file(file_id, file_name, parent_id):
    file_metadata = { 'name' : file_name }
    if(parent_id is not None):
      file_metadata['parents'] = [ parent_id ]
    try:
      service().files().copy(fileId=file_id, body=file_metadata).execute();
    except errors.HttpError as error:
      print ('An error occurred on copy file: %s' % error)



def delete_file(file_id):
  try:
    return service().files().delete(fileId=file_id).execute();
  except errors.HttpError as e:
    # print(e.__dict__)
    if e.resp.status != 404 :
      print("ERROR on get_file_info: " + str(e))
    return None



def get_list_files(list_id):
  search_result = []
  page_token = None
  while True:
    _search_query = "'" + list_id + "' in parents"
    _search_response = service().files().list(q=_search_query, spaces='drive', fields='nextPageToken, files(id,name,mimeType,parents)', pageToken=page_token).execute()
    search_result.extend(_search_response.get('files', []))

    page_token = _search_response.get('nextPageToken', None)
    if page_token is None:
        break;

  return search_result





### CLONE FUNCTIONS ###
def force_clone_file(file, parent_id):
  if(file['mimeType'] == 'application/vnd.google-apps.folder'):
    print("clone folder " + file['name'] + "...")

    new_folder_id = create_folder(file['name'], parent_id)
    for child_file in get_list_files(file['id']):
      force_clone_file(child_file, new_folder_id)

    print(file['name'] + " folder was cloned!")

  else :
    if(is_file_exist_on_my_drive(file['id'])):
      print(file['name'] + " is existed")
    else:
      print("copy file " + file['name'] + "...")
      copy_file(file['id'], file['name'], parent_id)
      print("copied file " + file['name'] + "!")





### PUSH FUNCTIONS ###
def upload_file(path, parent_id):
  file_name = os.path.basename(path)
  print("%s is uploading ..." % file_name)
  file_metadata = { 'name' : file_name }
  if(parent_id is not None):
    file_metadata['parents'] = [ parent_id ]
  retries = 0
  media = MediaFileUpload(path, mimetype='', chunksize=2048*512, resumable=True)
  request = service().files().create(body=file_metadata, media_body=media, fields='id')
  response = None
  while response is None:
    try:
      # print(http().request.credentials.access_token)
      status, response = request.next_chunk()
      if status:
        print("Uploaded %.2f%%" % (status.progress() * 100))
        retries = 0
    except errors.HttpError as e:
      if e.resp.status == 404:
        print("Error 404! Aborting.")
        exit()
      else:   
        if retries > 10:
          print("Retries limit exceeded! Aborting.")
          exit()
        else:   
          retries += 1
          time.sleep(2**retries)
          print("Error (%d)... retrying." % e.resp.status)
          continue
  print(file_name + " uploaded!")
  return response.get('id')




def push_file(path, parent_id) :
  file_name = os.path.basename(path)
  uploaded_file_id = upload_file(path, parent_id)
  print("pushed to your Driver file '%s' with id is %s" % (file_name, uploaded_file_id))



def push_folder(path, parent_id) :
  print("push folder '%s'..." % path)
  folder_name = os.path.basename(path)
  new_folder_id = create_folder(folder_name, parent_id)
  for f in os.listdir(path) :
    # print(f)
    file = os.path.join(path, f)
    if os.path.isfile(file) :
      push_file(file, new_folder_id)
    if os.path.isdir(file) :
      push_folder(file, new_folder_id)
  print("pushed folder %s" % path)






### PULL FUNCTIONS
def download_file(file_id, path) :
  file_info = get_file_info(file_id);
  path = os.path.join(path, file_info['name'])

  request = None

  # if file_info['mimeType'] in DOC_MIME_TYPES :
  #   request = service().files().export_media(fileId=file_id, mimeType=file_info['mimeType'] )
  # else :
  request = service().files().get_media(fileId=file_id)

  # fh = io.BytesIO()
  fh = io.FileIO(path, 'wb')
  downloader = MediaIoBaseDownload(fh, request, chunksize=2048*512)
  done = False

  while done is False:
    status, done = downloader.next_chunk()
    print("Download %d%%." % int(status.progress() * 100))

  # with open(path, "wb") as f:
  #   f.write(fh.getvalue())


def download_folder(folder_id, path) :
  folder_info = get_file_info(folder_id);
  path = os.path.join(path, folder_info['name'])
  if not os.path.exists(path) :
    os.makedirs(path)

  for file in get_list_files(folder_id) :
    file_info = get_file_info(file['id']);
    if file_info['mimeType'] == 'application/vnd.google-apps.folder' :
      download_folder(file_info['id'], path)

    else :
      download_file(file_info['id'], path)



### SEARCH FUNCTIONS ###
def search_folder(folder_name, parent_id):
  search_query = "mimeType='application/vnd.google-apps.folder' and trashed = false and 'me' in owners"
  if folder_name is not None :
    search_query += " and fullText contains '%s'" % (urllib.parse.quote_plus(folder_name))
  if(parent_id is not None):
    search_query += " and '%s' in parents" % parent_id

  return _search_by_query(search_query)




def search_file(file_name, parent_id):
  search_query = "mimeType != 'application/vnd.google-apps.folder' and trashed = false and 'me' in owners"
  if file_name is not None and file_name != "" :
    search_query += " and fullText contains '%s'" % (urllib.parse.quote_plus(file_name))
  if(parent_id is not None):
    search_query += " and '%s' in parents" % parent_id

  return _search_by_query(search_query)



def print_search(search_result) :
  if search_result == [] or search_result == None :
    print("No results!!!")
    return

  if hasattr(args, 'parent') and args.parent :
    print('{:3}{:72}{:^32}\t{:^48}'.format("#", "NAME - ID", "--- PARENT ---", "--- PARENT NAME ---"))
  else :
    print('{:3}{:52}{:^32}{:^32}'.format("#", "NAME", "--- ID ---", "--- PATH ---"))
  # else :
  #   print('{:52}{:^32}{:^32}'.format("# NAME", "--- ID ---", "--- PARENT ---"))

  for fo in search_result :
    if fo is None : continue
    if 'parents' not in fo:
      fo['parents'] = [ROOT_FOLDER_ID]

    file_type = "__"
    if fo['mimeType'] == 'application/vnd.google-apps.folder' :
      file_type = "d_"

    if hasattr(args, 'parent') and args.parent :
      parent_name = []
      for parent_id in fo['parents'] :
        if parent_id == ROOT_FOLDER_ID :
          parent_name.append(ROOT_FOLDER_ID)
          continue
        parent_name.append(get_file_info(parent_id)['name'])
      print('{:3}{:72}{:^32}\t{:64}'.format(file_type, "%s (%s)" % (fo['name'], fo['id']), str(fo['parents']), str(parent_name)))


    else :
      print('{:3}{:48}{:32}{:32}'.format(file_type, fo['name'], fo['id'], get_file_path(fo['id'], None)))

  return


### DO NOT USE NOW
# def search_in(folder) :
#   search_result = []
#   if args.all or args.folder : search_result.extend(search_folder(args.search_text, folder['id']))
#   if args.all or args.file : search_result.extend(search_file(args.search_text, folder['id']))
#   for p_child in get_list_files(folder['id']) :
#     search_result = search_in(p_child)

#   return search_result;






##### ADD USER #####
def add_user() :
  oauth_json_file = args.oauth_json_file
  user_id = args.user_id
  file_extension = JSON_EXTENSION
  file_name, file_extension = os.path.splitext(oauth_json_file)
  if user_id is None or user_id == "" :
    user_id = os.path.basename(file_name)

  if file_extension != JSON_EXTENSION :
    print("Invalid OAuth2.0 credentials json file")
    return

  # copy oauth json file to application dir
  oauth_data = {}
  user_json_file = os.path.join(APPLICATION_OAUTH_DIR, user_id + JSON_EXTENSION)
  with open(oauth_json_file) as json_data :
    oauth_data = json.load(json_data)
  with open(user_json_file, 'w') as fp:
    json.dump(oauth_data, fp, sort_keys=True, indent=4)

  # read json config file
  config_data = APPLICATION_CONFIGS
  if 'users' not in config_data :
    config_data['users'] = {}
  # update user config
  config_data['users'][user_id] = {'id' : user_id, 'json_file' : user_json_file}

  if args.default or 'default_user' not in config_data :
    config_data['default_user'] = user_id

  # write to config file
  with open(APPLICATION_CONFIG_FILE, 'w') as fp:
    json.dump(config_data, fp, sort_keys=True, indent=4)

  print("Added user '%s'!" % user_id)





##### SET USER #####
def set_user() :
  user_id = args.user_id
  config_data = APPLICATION_CONFIGS
  config_data['default_user'] = user_id

    # write to config file
  with open(APPLICATION_CONFIG_FILE, 'w') as fp:
    json.dump(config_data, fp, sort_keys=True, indent=4)

  print("Set user '%s' as default!" % user_id)




##### CREATE #####
def create_dir() :
  new_name = args.name
  new_name = new_name.strip(' /\\')

  if args.dir != None and args.dir != "" :
    parent_folder = args.dir
    new_name = parent_folder.strip('/\\') + "/" + new_name

  create_folder(new_name, ROOT_FOLDER_ID)





##### LIST #####
def list_file():
  # link option
  link = args.link
  if link is not None and link != "" :
    if(link == "" or len(link.split("/")) < 4 or link.split("/")[2] != "drive.google.com") :
      print("Invalid link")
      return

    if(link.split("/")[3] == "drive" and link.split("/")[4] == "folders") :
      print_search(get_list_files(link.split("/")[5]))
      # for item in get_list_files(link.split("/")[5]):
      #   print('{0} ({1}) --- in parent {2}'.format(item['name'], item['id'], item['parents']))

    return

  # id option
  list_id = args.id
  if list_id is not None and list_id != "" :
    search_query = "'%s' in parents" % list_id
    print_search(_search_by_query(search_query))

    return

  # directory option
  list_dir = args.dir
  if list_dir is not None and list_dir != "" :
    folder_id = find_folder(list_dir, ROOT_FOLDER_ID)
    if folder_id is not None :
      search_query = "'%s' in parents" % folder_id
      print_search(_search_by_query(search_query))
    else :
      print_search(None)

    return

  # no options
  search_query = "'%s' in parents" % ROOT_FOLDER_ID
  print_search(_search_by_query(search_query))

  return




##### CLONE #####
def clone():
  link = args.link
  force_copy = args.force_copy

  #process link
  if(link == "" or len(link.split("/")) < 4 or link.split("/")[2] != "drive.google.com") :
    print("Invalid link")
    return

  #process with folder
  if(link.split("/")[3] == "drive" and link.split("/")[4] == "folders") :
    clone_file_id = link.split("/")[5]

    file_info = get_file_info(clone_file_id)
    parent_folder_id = ROOT_FOLDER_ID
    if args.to_dir != None and args.to_dir != "" :
      parent_folder_id = create_folder(args.to_dir, ROOT_FOLDER_ID)
    
    parent_folder_id = create_folder(file_info['name'], parent_folder_id)
    for child_file in get_list_files(clone_file_id):
      force_clone_file(child_file, parent_folder_id)

  #process with file
  if(link.split("/")[3] == "file") :
    parent_folder_id = ROOT_FOLDER_ID
    if args.to_dir != None and args.to_dir != "":
      parent_folder_id = create_folder(args.to_dir, ROOT_FOLDER_ID)

    des_file = get_file_info(link.split("/")[5])
    copy_file(des_file['id'], des_file['name'], parent_folder_id)

  print("clone to your Driver from link " + link)




##### PUSH #####
def push():
  parent_id = ROOT_FOLDER_ID
  if args.to_dir != None and args.to_dir != "" :
    parent_id = create_folder(args.to_dir, ROOT_FOLDER_ID)


  # if args.file is not None :
  path = parse_path(args.path)
  if os.path.exists(path) and os.path.isfile(path) :
    push_file(path, parent_id)

  elif os.path.exists(path) and os.path.isdir(path) :
    push_folder(path, parent_id)
  else :
    print("Please choise file or path to push")





##### PULL #####
def pull() :
  path = args.path;
  path = path.strip(' \\/')

  to_dir = parse_path(".")
  if args.to_dir != None and args.to_dir != "" :
    to_dir = parse_path(args.to_dir)

  if(len(path.split("/")) > 1 or len(path.split("\\")) > 1):
    if(len(path.split("/")) > 1):
      list_folder_name = path.split("/")
    if(len(path.split("\\")) > 1):
      list_folder_name = path.split("\\")

    # is_file_name_in_my_drive(list_folder_name[len(list_folder_name) - 1], )
    parent_path = list_folder_name[:-1]
    parent_id = find_folder('/'.join(parent_path), ROOT_FOLDER_ID)
    file_name = list_folder_name[-1]
    if is_file_name_in_my_drive(file_name, parent_id) :
      download_file(get_file_info_by_name(file_name, parent_id)['id'], to_dir)

    if is_folder_exist_in_my_drive(file_name, parent_id) :
      download_folder(get_folder_info(file_name, parent_id)['id'], to_dir)

  else :
    if is_file_name_in_my_drive(path, ROOT_FOLDER_ID) :
      download_file(get_file_info_by_name(path, ROOT_FOLDER_ID)['id'], to_dir)

    if is_folder_exist_in_my_drive(path, ROOT_FOLDER_ID) :
      download_folder(get_folder_info(path, ROOT_FOLDER_ID)['id'], to_dir)




##### SEARCH #####
def search():
  if args.file or args.folder : args.all = False

  if args.dir != None and args.dir != "" :
    folder_name = args.dir
    parent_folder = []
    parent_folder_id = ROOT_FOLDER_ID
    if(len(folder_name.split("/")) > 1 or len(folder_name.split("\\")) > 1):
      if(len(folder_name.split("/")) > 1):
        list_folder_name = folder_name.split("/")
      if(len(folder_name.split("\\")) > 1):
        list_folder_name = folder_name.split("\\")

      for f_name in list_folder_name :
        if not is_folder_exist_in_my_drive(f_name, parent_folder_id) :
          parent_folder = []
          break
        
        parent_folder = get_folder_info(f_name, parent_folder_id)
        parent_folder_id = parent_folder['id']

    else :
      parent_folder = get_folder_info(folder_name, parent_folder_id)


    print("Result in '%s':" % folder_name)
    if not parent_folder :
      print_search(None)
      return
    search_result = []

    if args.search_text is not None :
      # search_result.extend(search_in(parent_folder))
      if args.all or args.folder : search_result.extend(search_folder(args.search_text, parent_folder['id']))
      if args.all or args.file : search_result.extend(search_file(args.search_text, parent_folder['id']))
      print_search(search_result)

    if args.search_id is not None :
      search_result = get_file_info(args.search_id);
      if search_result is None :
        print_search(search_result)
      else :
        if parent_folder['id'] in search_result['parents'] :
          print_search([search_result])
        else :
          print_search(None)


  else :
    print("Result:")
    if args.search_text != None :
      search_result = []
      if args.all or args.folder : search_result.extend(search_folder(args.search_text, None))
      if args.all or args.file : search_result.extend(search_file(args.search_text, None))

      print_search(search_result)

      # print(search_folder(args.search_key, None))

    if args.search_id != None :
      search_result = get_file_info(args.search_id);
      if search_result is None :
        print_search(search_result)
      else :
        print_search([search_result])

      return



##### DELETE
def delete() :
  path = args.path
  path = path.strip(' \\/')

  if(len(path.split("/")) > 1 or len(path.split("\\")) > 1):
    if(len(path.split("/")) > 1):
      list_folder_name = path.split("/")
    if(len(path.split("\\")) > 1):
      list_folder_name = path.split("\\")

    # is_file_name_in_my_drive(list_folder_name[len(list_folder_name) - 1], )
    parent_path = list_folder_name[:-1]
    parent_id = find_folder('/'.join(parent_path), ROOT_FOLDER_ID)
    file_name = list_folder_name[-1]
    if is_file_name_in_my_drive(file_name, parent_id) :
      delete_file(get_file_info_by_name(file_name, parent_id)['id'])
    if is_folder_exist_in_my_drive(file_name, parent_id) :
      delete_file(get_folder_info(file_name, parent_id)['id'])

  else :
    if is_file_name_in_my_drive(path, ROOT_FOLDER_ID) :
      delete_file(get_file_info_by_name(path, ROOT_FOLDER_ID)['id'])

    if is_folder_exist_in_my_drive(path, ROOT_FOLDER_ID) :
      delete_file(get_folder_info(path, ROOT_FOLDER_ID)['id'])

  print("'%s' deleted!" % path)



##### RESET #####
def reset_app() :
  if os.path.exists(APPLICATION_CONFIG_FILE) :
    with open(APPLICATION_CONFIG_FILE, 'w') as fp:
      json.dump({}, fp, sort_keys=True, indent=4)

  # remove credential files
  for root, dirs, files in os.walk(APPLICATION_CREDENTIALS_DIR, topdown=False):
    for name in files:
        os.remove(os.path.join(root, name))
    for name in dirs:
        os.rmdir(os.path.join(root, name))

  # remove oauth files
  for root, dirs, files in os.walk(APPLICATION_OAUTH_DIR, topdown=False):
    for name in files:
        os.remove(os.path.join(root, name))
    for name in dirs:
        os.rmdir(os.path.join(root, name))

  print("All application configuration is cleared. Please add user to continue!")






######### MAIN APPLICATION #######
def parse_path(path):
  return os.path.abspath(os.path.expanduser(path))

def main():

  command = args.command;
  if(command == None) :
    return

  if not os.path.exists(APPLICATION_DIR):
      os.makedirs(APPLICATION_DIR)
  if not os.path.exists(APPLICATION_CREDENTIALS_DIR):
      os.makedirs(APPLICATION_CREDENTIALS_DIR)
  if not os.path.exists(APPLICATION_OAUTH_DIR):
      os.makedirs(APPLICATION_OAUTH_DIR)

  global CURRENT_USER_ID
  global DEFAULT_USER_ID
  global APPLICATION_CONFIGS
  CURRENT_USER_ID = args.user
  APPLICATION_CONFIGS = get_app_configs()

  if 'default_user' in APPLICATION_CONFIGS :
    DEFAULT_USER_ID = APPLICATION_CONFIGS['default_user']
  if CURRENT_USER_ID is None or CURRENT_USER_ID == '' :
    CURRENT_USER_ID = DEFAULT_USER_ID

  if (command != 'adduser' and command != 'setuser') and (CURRENT_USER_ID == '' or not get_user_infor(CURRENT_USER_ID)) :
    print("Invalid user")
    return


  print("======== Execute Command '%s' =========" % command)
  args.execute_command()



try:
  import argparse
  arg_parser = argparse.ArgumentParser(parents=[tools.argparser])
  arg_parser.add_argument('-u', '--user', help='Google user account will be use')
  _sub_arg_parser = arg_parser.add_subparsers(dest='command', help='Command to execute', metavar="COMMAND")

  parser_adduser = _sub_arg_parser.add_parser('adduser', help='Add an user to Google Drive Tool')
  parser_adduser.add_argument('-f', '--oauth-json-file', help='OAuth2.0 credentials json file', dest="oauth_json_file")
  parser_adduser.add_argument('-i', '--user-id', help='User sort name to used on command', dest="user_id")
  parser_adduser.add_argument('-d', '--default', help="Set new user as default", action='store_true', default=False)
  parser_adduser.set_defaults(execute_command=add_user)

  parser_setuser = _sub_arg_parser.add_parser('setuser', help='Set an user as default')
  parser_setuser.add_argument('user_id', help='User ID')
  parser_setuser.set_defaults(execute_command=set_user)

  parser_create = _sub_arg_parser.add_parser('create', help='Create new folder/directory')
  parser_create.add_argument('name', help='New folder name')
  parser_create.add_argument('-d', '--dir', help="Parent folder")
  parser_create.set_defaults(execute_command=create_dir)

  parser_delete = _sub_arg_parser.add_parser('delete', help='Delete a folder or a file')
  parser_delete.add_argument('path', help='Path to delete')
  parser_delete.set_defaults(execute_command=delete)

  parser_list = _sub_arg_parser.add_parser('list', help='List of drive files')
  parser_list.add_argument('-d', '--dir', help='List of a directory name')
  parser_list.add_argument('-i', '--id', help='List of a drive ID')
  parser_list.add_argument('-l', '--link', help='List of a link')
  parser_list.set_defaults(execute_command=list_file)

  parser_clone = _sub_arg_parser.add_parser('clone', help='Clone a public drive to your drive')
  parser_clone.add_argument('link', help='Link of the public drive')
  parser_clone.add_argument('-f', '--force-copy', help='Copy file as you are owner', action="store_true", default=True, dest="force_copy")
  parser_clone.add_argument('-t', '--to-dir', help='The folder to save', dest='to_dir')
  parser_clone.set_defaults(execute_command=clone)

  parser_push = _sub_arg_parser.add_parser('push', help='Push file to your drive')
  parser_push.add_argument('path', help='Path  to push')
  parser_push.add_argument('-t', '--to-dir', help='The folder to save', dest='to_dir')
  parser_push.set_defaults(execute_command=push)

  parser_pull = _sub_arg_parser.add_parser('pull', help='Download from Drive to local')
  parser_pull.add_argument('path', help='Path to pull')
  parser_pull.add_argument('-t', '--to-dir', help='The folder to save', dest='to_dir')
  parser_pull.set_defaults(execute_command=pull)

  parser_search = _sub_arg_parser.add_parser('search', help='Search file in your drive')
  search_key_group = parser_search.add_mutually_exclusive_group(required=True);
  search_key_group.add_argument('-s', help="Text to search", default=None, dest='search_text')
  search_key_group.add_argument('-i', help="ID to search", default=None, dest='search_id')
  parser_search.add_argument('-d', '--dir', help="Folder to searching in")
  search_type_group = parser_search.add_mutually_exclusive_group();
  search_type_group.add_argument('-f', '--file', help="Search file only", action='store_true', default=False)
  search_type_group.add_argument('-o', '--folder', help="Search folder only", action='store_true', default=False)
  search_type_group.add_argument('-a', '--all', help="Search both file and folder", action='store_true', default=True)
  parser_search.add_argument('-p', '--parent', help="Show parent information only", action='store_true')
  parser_search.set_defaults(execute_command=search)

  parser_reset = _sub_arg_parser.add_parser('reset', help='Rerset Google Drive Tool configurations')
  parser_reset.set_defaults(execute_command=reset_app)

  args = arg_parser.parse_args()
except ImportError:
  args = None

if __name__ == '__main__':
    main()
