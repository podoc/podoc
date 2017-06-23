# -*- coding: utf-8 -*-

"""Tests for the Notebook contents manager.

Taken from https://github.com/jupyter/notebook/blob/master/notebook/services/contents/tests/test_manager.py  # noqa

"""

#-------------------------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------------------------

from itertools import combinations
from tempfile import TemporaryDirectory

from tornado.web import HTTPError
import notebook.services.contents.tests.test_manager as tm

from ..manager import PodocContentsManager

# Monkey patch Jupyter's FileContentsManager with podoc's class.
tm.FileContentsManager = PodocContentsManager


#-------------------------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------------------------

class TestPodocFileContentsManager(tm.TestFileContentsManager):
    pass


class TestPodocContentsManager(tm.TestContentsManager):

    def make_populated_dir(self, api_path):
        cm = self.contents_manager

        self.make_dir(api_path)

        cm.new(path="/".join([api_path, "nb.ipynb"]))
        cm.new(path="/".join([api_path, "file.txt"]))

        # Ideally this one should *not* be interpreted as an AST...
        cm.new(path="/".join([api_path, "file.json"]))

        # Add a Markdown file. It should be detected as a notebook.
        cm.new(path="/".join([api_path, "markdown.md"]))

    def check_populated_dir_files(self, api_path):
        dir_model = self.contents_manager.get(api_path)

        self.assertEqual(dir_model['path'], api_path)
        self.assertEqual(dir_model['type'], "directory")

        for entry in dir_model['content']:
            if entry['type'] == "directory":
                continue
            elif entry['type'] == "file":
                assert entry['name'] in ('file.txt', 'file.json')
                complete_path = "/".join([api_path, entry['name']])
                self.assertEqual(entry["path"], complete_path)
            elif entry['type'] == "notebook":
                # The notebook is either the .ipynb or .md file.
                assert entry['name'] in ('nb.ipynb', 'markdown.md')
                complete_path = "/".join([api_path, entry['name']])
                self.assertEqual(entry["path"], complete_path)

    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        self.td = self._temp_dir.name
        self.contents_manager = PodocContentsManager(
            root_dir=self.td,
        )

    def test_get(self):
        super(TestPodocContentsManager, self).test_get()
        cm = self.contents_manager

        # Test in sub-directory
        sub_dir = '/foo/'
        self.make_dir('foo')
        # Use the .md extension.
        model = cm.new_untitled(path=sub_dir, ext='.md')
        model2 = cm.get(sub_dir + model['name'])
        assert isinstance(model2, dict)
        self.assertIn('name', model2)
        self.assertIn('path', model2)
        self.assertIn('content', model2)
        self.assertEqual(model2['name'], 'Untitled.md')
        self.assertEqual(model2['path'], '{0}/{1}'.format(sub_dir.strip('/'), model['name']))

    def test_update_md(self):
        cm = self.contents_manager
        # Create a notebook
        model = cm.new_untitled(type='notebook')
        path = model['path']

        # Change the name in the model for rename
        model['path'] = 'test.md'
        model = cm.update(model, path)
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertEqual(model['name'], 'test.md')

        # Make sure the old name is gone
        self.assertRaises(HTTPError, cm.get, path)

        # Test in sub-directory
        # Create a directory and notebook in that directory
        sub_dir = '/foo/'
        self.make_dir('foo')
        model = cm.new_untitled(path=sub_dir, type='notebook')
        path = model['path']

        # Change the name in the model for rename
        d = path.rsplit('/', 1)[0]
        new_path = model['path'] = d + '/test_in_sub.md'
        model = cm.update(model, path)
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertEqual(model['name'], 'test_in_sub.md')
        self.assertEqual(model['path'], new_path)

        # Make sure the old name is gone
        self.assertRaises(HTTPError, cm.get, path)

    def test_save_md(self):
        cm = self.contents_manager
        # Create a notebook
        model = cm.new_untitled(type='notebook', ext='.md')
        name = model['name']
        path = model['path']

        # Get the model with 'content'
        full_model = cm.get(path)

        # Save the notebook
        model = cm.save(full_model, path)
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertEqual(model['name'], name)
        self.assertEqual(model['path'], path)

        # Test in sub-directory
        # Create a directory and notebook in that directory
        sub_dir = '/foo/'
        self.make_dir('foo')
        model = cm.new_untitled(path=sub_dir, type='notebook', ext='.md')
        name = model['name']
        path = model['path']
        model = cm.get(path)

        # Change the name in the model for rename
        model = cm.save(model, path)
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertEqual(model['name'], 'Untitled.md')
        self.assertEqual(model['path'], 'foo/Untitled.md')

    def test_rename_md(self):
        cm = self.contents_manager
        # Create a new notebook
        nb, name, path = self.new_notebook()

        # Rename the notebook
        cm.rename(path, "changed_path")

        # Attempting to get the notebook under the old name raises an error
        self.assertRaises(HTTPError, cm.get, path)
        # Fetching the notebook under the new name is successful
        assert isinstance(cm.get("changed_path"), dict)

        # Ported tests on nested directory renaming from pgcontents
        all_dirs = ['foo', 'bar', 'foo/bar', 'foo/bar/foo', 'foo/bar/foo/bar']
        unchanged_dirs = all_dirs[:2]
        changed_dirs = all_dirs[2:]

        for _dir in all_dirs:
            self.make_populated_dir(_dir)
            self.check_populated_dir_files(_dir)

        # Renaming to an existing directory should fail
        for src, dest in combinations(all_dirs, 2):
            with self.assertRaisesHTTPError(409):
                cm.rename(src, dest)

        # Creating a notebook in a non_existant directory should fail
        with self.assertRaisesHTTPError(404):
            cm.new_untitled("foo/bar_diff", ext=".md")

        cm.rename("foo/bar", "foo/bar_diff")

        # Assert that unchanged directories remain so
        for unchanged in unchanged_dirs:
            self.check_populated_dir_files(unchanged)

        # Assert changed directories can no longer be accessed under old names
        for changed_dirname in changed_dirs:
            with self.assertRaisesHTTPError(404):
                cm.get(changed_dirname)

            new_dirname = changed_dirname.replace("foo/bar", "foo/bar_diff", 1)

            self.check_populated_dir_files(new_dirname)

        # Created a notebook in the renamed directory should work
        cm.new_untitled("foo/bar_diff", ext=".md")

    def test_copy_md(self):
        cm = self.contents_manager
        parent = u'å b'
        name = u'nb √.md'
        path = u'{0}/{1}'.format(parent, name)
        self.make_dir(parent)

        orig = cm.new(path=path)
        # copy with unspecified name
        copy = cm.copy(path)
        self.assertEqual(copy['name'], orig['name'].replace(
            '.md', '-Copy1.md'))

        # copy with specified name
        copy2 = cm.copy(path, u'å b/copy 2.md')
        self.assertEqual(copy2['name'], u'copy 2.md')
        self.assertEqual(copy2['path'], u'å b/copy 2.md')
        # copy with specified path
        copy2 = cm.copy(path, u'/')
        self.assertEqual(copy2['name'], name)
        self.assertEqual(copy2['path'], name)
