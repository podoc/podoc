# -*- coding: utf-8 -*-

"""Notebook contents manager."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
import os
import os.path as op

from tornado import web
import nbformat
from traitlets import Unicode, Bool
from traitlets.config import Configurable
from notebook.services.contents.filemanager import FileContentsManager

from podoc.core import Podoc
from ._notebook import new_notebook

logger = logging.getLogger(__name__)


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
        elif file_ext == '.ipynb':
            return True
        elif file_ext in p.file_extensions:
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
            logger.debug("%s is a directory.", os_path)
            model = self._dir_model(path, content=content)
        elif (type == 'notebook' or (type is None and use_podoc)):
            logger.debug("%s is a notebook.", os_path)
            model = self._notebook_model(path, content=content)
        else:
            if type == 'directory':  # pragma: no cover
                raise web.HTTPError(400, u'%s is not a directory',
                                    reason='bad type')
            logger.debug("%s is a static file.", os_path)
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
                                               )

            except Exception as e:  # pragma: no cover
                logger.exception(e)
                raise web.HTTPError(
                    400,
                    u"Unreadable Notebook: %s %r" % (os_path, e),
                )

    def save(self, model, path=''):
        """Save the file model and return the model with no content."""
        path = path.strip('/')

        if 'type' not in model:  # pragma: no cover
            raise web.HTTPError(400, u'No file type provided')
        if ('content' not in model and
                model['type'] != 'directory'):  # pragma: no cover
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
            else:  # pragma: no cover
                raise web.HTTPError(400, "Unhandled contents type: %s" % model['type'])  # noqa
        except web.HTTPError:  # pragma: no cover
            raise
        except Exception as e:  # pragma: no cover
            self.log.error(u'Error while saving file: %s %s', path, e, exc_info=True)  # noqa
            raise web.HTTPError(500, u'Unexpected error while saving file: %s %s' % (path, e))  # noqa

        validation_message = None
        if model['type'] == 'notebook':
            self.validate_notebook_model(model)
            validation_message = model.get('message', None)

        model = self.get(path, content=False)
        if validation_message:  # pragma: no cover
            model['message'] = validation_message

        self.run_post_save_hook(model=model, os_path=os_path)

        return model

    def new_untitled(self, path='', type='', ext=''):
        """Create a new untitled file or directory in path

        path must be a directory

        File extension can be specified.

        Use `new` to create files with a fully specified path
        (including filename).

        """
        path = path.strip('/')
        if not self.dir_exists(path):
            raise web.HTTPError(404, 'No such directory: %s' % path)

        model = {}
        if type:
            model['type'] = type

        # if ext == '.ipynb':
        if self._do_use_podoc(ext):
            model.setdefault('type', 'notebook')
        else:
            model.setdefault('type', 'file')

        insert = ''
        if model['type'] == 'directory':
            untitled = self.untitled_directory
            insert = ' '
        elif model['type'] == 'notebook':
            untitled = self.untitled_notebook
            ext = ext or '.ipynb'
        elif model['type'] == 'file':
            untitled = self.untitled_file
        else:  # pragma: no cover
            raise web.HTTPError(400,
                                "Unexpected model type: %r" % model['type'])

        name = self.increment_filename(untitled + ext, path, insert=insert)
        path = u'{0}/{1}'.format(path, name)
        return self.new(model, path)

    def new(self, model=None, path=''):
        """Create a new file or directory and return its model with no content.

        To create a new untitled entity in a directory, use `new_untitled`.
        """
        path = path.strip('/')
        if model is None:
            model = {}

        # if path.endswith('.ipynb'):
        if self._do_use_podoc(op.splitext(path)[1]):
            model.setdefault('type', 'notebook')
        else:
            model.setdefault('type', 'file')

        # no content, not a directory, so fill out new-file model
        if 'content' not in model and model['type'] != 'directory':
            if model['type'] == 'notebook':
                model['content'] = new_notebook()
                model['format'] = 'json'
            else:
                model['content'] = ''
                model['type'] = 'file'
                model['format'] = 'text'

        model = self.save(model, path)
        return model
