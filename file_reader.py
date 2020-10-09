
class FileReader:

    def __init__(self):
        pass

    def get(self, filepath, cookies):
        try:
            file = open(filepath, 'rb')
            return file.read()
        except IsADirectoryError:
            filepath_webpage = '<html><body><h1>{}</h1></body></html>'.format(filepath)
            return filepath_webpage.encode()
        except:
            return None


    def head(self, filepath, cookies):
        try:
            print("looking for file: " + filepath)
            file = open(filepath, 'rb')
            return len(file.read())
        except IsADirectoryError:
            filepath_webpage = '<html><body><h1>{}</h1></body></html>'.format(filepath)
            return len(filepath_webpage.encode())
        except:
            return None