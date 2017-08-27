
from __future__ import print_function
import httplib2
import os
import sys
import mimetypes
import urllib.parse

from apiclient import discovery
from apiclient import errors
from apiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

args = None



# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'ian.json'
ACCOUNT = 'ian'
APPLICATION_NAME = 'Drive API Python Tool'
CREDENTIAL_PATH = ''
ROOT_FOLDER_ID = 'root'


def get_credentials():
  home_dir = os.path.expanduser('~')
  credential_dir = os.path.join(home_dir, '.credentials')
  if not os.path.exists(credential_dir):
      os.makedirs(credential_dir)
  CREDENTIAL_PATH = os.path.join(credential_dir,
                                 'drive-python-' + ACCOUNT + '.json')

  store = Storage(CREDENTIAL_PATH)
  credentials = store.get()
  if not credentials or credentials.invalid:
      flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
      flow.user_agent = APPLICATION_NAME
      if args:
        credentials = tools.run_flow(flow, store, args)
      else: # Needed only for compatibility with Python 2.6
          credentials = tools.run(flow, store)
      print('Storing credentials to ' + CREDENTIAL_PATH)
  return credentials

def http():
  credentials = get_credentials()
  http = credentials.authorize(httplib2.Http())
  return http

def service():
  service = discovery.build('drive', 'v3', http=http())
  return service





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
    print("ERROR on search_file: " + str(e))
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
  search_query += "fullText contains '" + urllib.parse.quote_plus(folder_name) + "'"
  if(parent_id is not None):
    search_query += " and '" + parent_id + "' in parents"
  
  folder_info = _search_by_query(search_query)
  if not folder_info :
    return []

  return folder_info[0]




def search_folder(folder_name, parent_id):
  search_query = "mimeType='application/vnd.google-apps.folder' and trashed = false and 'me' in owners"
  if folder_name is not None :
    search_query += " and fullText contains '" + urllib.parse.quote_plus(folder_name) + "'"
  if(parent_id is not None):
    search_query += " and '" + parent_id + "' in parents"

  return _search_by_query(search_query)


def search_file(file_name, parent_id):
  search_query = "mimeType != 'application/vnd.google-apps.folder' and trashed = false and 'me' in owners"
  if file_name is not None and file_name != "" :
    search_query += " and fullText contains '" + urllib.parse.quote_plus(file_name) + "'"
  if(parent_id is not None):
    search_query += " and '" + parent_id + "' in parents"

  return _search_by_query(search_query)


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




def get_file_path(file_id, all_folders) :
  # file_info = None
  # if all_folders is not None :
  #   for cur_folder in all_folders :
  #     print(cur_folder['id'] + " --- " + file_id)
  #     if cur_folder['id'] == file_id :
  #       file_info = cur_folder
  #       break
  # else :
  #   all_folders = search_file(None, None)
  #   file_info = get_file_info(file_id);
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



def upload_file(path, parent_id):
  file_name = os.path.basename(path)
  print(file_name + " is uploading ...")
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



##### LIST #####
def list_file():
  # https://drive.google.com/drive/folders/0B-PgH1laJhKsdEh5TThoYklPblU
  link = args.link
  if link != "" :
    if(link == "" or len(link.split("/")) < 4 or link.split("/")[2] != "drive.google.com") :
      print("Invalid link")
      return

    if(link.split("/")[3] == "drive" and link.split("/")[4] == "folders") :
      for item in get_list_files(link.split("/")[5]):
        print('{0} ({1}) --- in parent {2}'.format(item['name'], item['id'], item['parents']))

    return

  page_token = None
  list_files = []
  while True:
    results = service().files().list(pageSize=1000,fields="nextPageToken, files(id, name)", pageToken=page_token).execute()
    list_files.extend(results.get('files', []))
    page_token = results.get('nextPageToken', None)
    if page_token is None:
        break

  if not list_files:
      print('No files found.')
  else:
      print('Files:')
      for item in list_files:
          print('{0} ({1})'.format(item['name'], item['id']))
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


def push_file(path, parent_id) :
  file_name = os.path.basename(path)
  uploaded_file_id = upload_file(path, parent_id)
  print("pushed to your Driver file " + file_name + " with id is " + uploaded_file_id)



def push_folder(path, parent_id) :
  print("push folder " + path + "...")
  folder_name = os.path.basename(path)
  new_folder_id = create_folder(folder_name, parent_id)
  for f in os.listdir(path) :
    # print(f)
    file = os.path.join(path, f)
    if os.path.isfile(file) :
      push_file(file, new_folder_id)
    if os.path.isdir(file) :
      push_folder(file, new_folder_id)
  print("pushed folder " + path)

##### PUSH #####
def push():
  parent_id = ROOT_FOLDER_ID
  if args.to_dir != None and args.to_dir != "" :
    parent_id = create_folder(args.to_dir, ROOT_FOLDER_ID)


  # if args.file is not None :
  path = parse_path(args.path)
  if os.path.exists(path) and os.path.isfile(path) :
    push_file(path, parent_id)
  # else :
  #   print("Please choise file to push")

  # if args.dir is not None :
  # path = parse_path(args.path)
  elif os.path.exists(path) and os.path.isdir(path) :
    push_folder(path, parent_id)
  else :
    print("Please choise file or path to push")




def print_search(search_result) :
  if search_result == [] or search_result == None : 
    print("No results!!!")
    return

  if args.parent :
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

    if args.parent :
      parent_name = []
      for parent_id in fo['parents'] :
        if parent_id == ROOT_FOLDER_ID : 
          parent_name.append(ROOT_FOLDER_ID)
          continue
        parent_name.append(get_file_info(parent_id)['name'])
      print('{:3}{:72}{:^32}\t{:64}'.format(file_type, fo['name'] + " (" + fo['id'] + ")", str(fo['parents']), str(parent_name)))


    else :
      print('{:3}{:48}{:32}{:^32}'.format(file_type, fo['name'], fo['id'], get_file_path(fo['id'], None)))

  return



def search_in(folder) :
  search_result = []
  if args.all or args.folder : search_result.extend(search_folder(args.search_text, folder['id']))
  if args.all or args.file : search_result.extend(search_file(args.search_text, folder['id']))
  for p_child in get_list_files(folder['id']) :
    search_result = search_in(p_child)

  return search_result;



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


    print("Result in '" + folder_name + "':")
    if not parent_folder :
      print_search(None)
      return
    search_result = []

    if args.search_text is not None :
      # search_result.extend(search_in(parent_folder))
      if args.all or args.folder : search_result.extend(search_folder(args.search_text, parent_folder['id']))
      if args.all or args.file : search_result.extend(search_file(args.search_text, parent_folder['id']))
      for p_id in get_list_files(parent_folder['id']) :
        if args.all or args.folder : search_result.extend(search_folder(args.search_text, p_id['id']))
        if args.all or args.file : search_result.extend(search_file(args.search_text, p_id['id']))

      print_search(search_result)

    if args.search_id is not None :
      search_result = get_file_info(args.search_id);
      if search_result is None :
        print_search(search_result)
      else :
        if parent_folder['id'] in search_result[parents] :
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



#########
# def find_method_by_command(c):
#   return {
#     'list' : 'list_file',
#     'clone': 'clone',
#     'push': 'push'
#   }.get(c, "print_invalid_command")

# def print_invalid_command():
#   print("Invalid command")

# def parse_agrument(n):
#   args_len = len(sys.argv)
#   if(args_len < n + 1):
#     print_invalid_command()
#     return;

#   args = {}
#   for arg in sys.argv :
#     if(arg[0:2] == "--"): arg = arg[2:len(arg)]
#     if(arg[0] == "-"): arg = arg[1:len(arg)]
    
#     key = arg.split("=")[0]
#     value = True;
#     if(len(arg.split("=")) > 1):
#       key = arg.split("=")[0]
#       value = arg.split("=")[1]
#     args[key] = value

#   return args;

def parse_path(path):
  return os.path.abspath(os.path.expanduser(path))

def main():

  command = args.command;
  if(command == None): return

  global ACCOUNT
  global CLIENT_SECRET_FILE
  ACCOUNT = args.user
  CLIENT_SECRET_FILE = ACCOUNT + ".json"

  print("======== Execute command " + command + " =========")
  args.func()



try:
  import argparse
  arg_parser = argparse.ArgumentParser(parents=[tools.argparser])
  arg_parser.add_argument('-u', '--user', help='Account will be use', required=True)
  _sub_arg_parser = arg_parser.add_subparsers(dest='command', help='Command to execute', metavar="COMMAND")

  parser_list = _sub_arg_parser.add_parser('list', help='List of drive files')
  parser_list.add_argument('-l', '--link', help='Link of the public drive')
  parser_list.set_defaults(func=list_file)

  parser_clone = _sub_arg_parser.add_parser('clone', help='Clone a public drive to your drive')
  parser_clone.add_argument('-l', '--link', help='Link of the public drive', required=True)
  parser_clone.add_argument('-f', '--force_copy', help='Copy file as you are owner', action="store_true", default=True)
  parser_clone.add_argument('-t', '--to_dir', help='The folder to save')
  parser_clone.set_defaults(func=clone)

  parser_push = _sub_arg_parser.add_parser('push', help='Push file to your drive')
  parser_push.add_argument('path', help='Path  to push')
  # push_type_group = parser_push.add_mutually_exclusive_group(required=True);
  # push_type_group.add_argument('-f', '--file', help="The file will be push")
  # push_type_group.add_argument('-d', '--dir', help="The folder will be push")
  # parser_push.add_argument('-l', '--link', help="The link will be push")
  parser_push.add_argument('-t', '--to_dir', help='The folder to save')
  parser_push.set_defaults(func=push)

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
  parser_search.set_defaults(func=search)

  args = arg_parser.parse_args()
except ImportError:
  args = None

if __name__ == '__main__':
    main()
