# -*- coding: utf-8 -*-

"""Notebook contents manager."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os
import os.path as op

from tornado import web
from six.moves.urllib.error import HTTPError
import nbformat
from traitlets import Unicode, Bool
from traitlets.config import Configurable
from notebook.services.contents.filemanager import FileContentsManager

from podoc.core import Podoc


#------------------------------------------------------------------------------
# MarkdownContentsManager
#------------------------------------------------------------------------------

def _file_extension(os_path):
    return op.splitext(os_path)[1]


class PodocContentsManager(FileContentsManager, Configurable):
    # The name of the default kernel: if left blank, assume native (pythonX),
    # won't store kernelspec/language_info unless forced with verbose_metadata.
    # This will be passed to the FormatManager, overwriting any config there.
    default_kernel_name = Unicode(config=True)

    # Don't strip any metadata.
    # This will be passed to the FormatManager, overwriting any config there.
    verbose_metadata = Bool(False, config=True)

    def __init__(self, *args, **kwargs):
        super(PodocContentsManager, self).__init__(*args, **kwargs)

        self._podoc = Podoc()

    def _do_use_podoc(self, file_ext):
        """Determine whether podoc can convert a file extension to a
        notebook."""
        p = self._podoc
        # NOTE: skip JSON files which are probably not notebooks.
        if file_ext == '.json':
            return False
        if file_ext in p.file_extensions:
            lang = p.get_lang_for_file_ext(file_ext)
            return ('notebook' in p.get_target_languages(lang) and
                    lang in p.get_target_languages('notebook'))
        return False

    def get(self, path, content=True, type=None, format=None):
        """ Takes a path for an entity and returns its model

        Parameters
        ----------
        path : str
            the API path that describes the relative path for the target
        content : bool
            Whether to include the contents in the reply
        type : str, optional
            The requested type - 'file', 'notebook', or 'directory'.
            Will raise HTTPError 400 if the content doesn't match.
        format : str, optional
            The requested format for file contents. 'text' or 'base64'.
            Ignored if this returns a notebook or directory model.

        Returns
        -------
        model : dict
            the contents model. If content=True, returns the contents
            of the file or directory as well.
        """
        path = path.strip('/')

        if not self.exists(path):
            raise web.HTTPError(404, u'No such file or directory: %s' % path)

        os_path = self._get_os_path(path)
        file_ext = _file_extension(os_path)

        # Determine from the file extension whether Podoc knows about the
        # format, and if it can be converted to a notebook.
        use_podoc = self._do_use_podoc(file_ext)

        if os.path.isdir(os_path):
            if type not in (None, 'directory'):
                raise web.HTTPError(400, u'%s is a directory, not a %s' % (path, type), reason='bad type')  # noqa
            model = self._dir_model(path, content=content)
        elif (type == 'notebook' or (type is None and use_podoc)):
            model = self._notebook_model(path, content=content)
        else:
            if type == 'directory':
                raise web.HTTPError(400, u'%s is not a directory', reason='bad type')  # noqa
            model = self._file_model(path, content=content, format=format)
        return model

    def _read_notebook(self, os_path, as_version=4):
        """Read a notebook from an os path."""
        with self.open(os_path, 'r', encoding='utf-8') as f:
            try:

                file_ext = _file_extension(os_path)

                if file_ext == '.ipynb':
                    return nbformat.read(f, as_version=as_version)
                else:
                    # TODO: static resources (images)
                    lang = self._podoc.get_lang_for_file_ext(file_ext)
                    return self._podoc.convert(os_path,
                                               source=lang,
                                               target='notebook',
                                               resources=None,  # TODO
                                               )

            except Exception as e:
                raise HTTPError(
                    400,
                    u"Unreadable Notebook: %s %r" % (os_path, e),
                )

    def save(self, model, path=''):
        """Save the file model and return the model with no content."""
        path = path.strip('/')

        if 'type' not in model:
            raise web.HTTPError(400, u'No file type provided')
        if 'content' not in model and model['type'] != 'directory':
            raise web.HTTPError(400, u'No file content provided')

        self.run_pre_save_hook(model=model, path=path)

        os_path = self._get_os_path(path)
        self.log.debug("Saving %s", os_path)
        try:
            if model['type'] == 'notebook':

                file_ext = _file_extension(os_path)
                nb = nbformat.from_dict(model['content'])
                if file_ext == '.ipynb':
                    self.check_and_sign(nb, path)
                    self._save_notebook(os_path, nb)
                else:
                    p = self._podoc
                    lang = p.get_lang_for_file_ext(file_ext)
                    p.convert(nb,
                              source='notebook',
                              target=lang,
                              resources=None,  # TODO
                              output=os_path,
                              )

                # One checkpoint should always exist for notebooks.
                if not self.checkpoints.list_checkpoints(path):
                    self.create_checkpoint(path)
            elif model['type'] == 'file':
                # Missing format will be handled internally by _save_file.
                self._save_file(os_path, model['content'], model.get('format'))
            elif model['type'] == 'directory':
                self._save_directory(os_path, model, path)
            else:
                raise web.HTTPError(400, "Unhandled contents type: %s" % model['type'])  # noqa
        except web.HTTPError:
            raise
        except Exception as e:
            self.log.error(u'Error while saving file: %s %s', path, e, exc_info=True)  # noqa
            raise web.HTTPError(500, u'Unexpected error while saving file: %s %s' % (path, e))  # noqa

        validation_message = None
        if model['type'] == 'notebook':
            self.validate_notebook_model(model)
            validation_message = model.get('message', None)

        model = self.get(path, content=False)
        if validation_message:
            model['message'] = validation_message

        self.run_post_save_hook(model=model, os_path=os_path)

        return model
