.. This Software (Dioptra) is being made available as a public service by the
.. National Institute of Standards and Technology (NIST), an Agency of the United
.. States Department of Commerce. This software was developed in part by employees of
.. NIST and in part by NIST contractors. Copyright in portions of this software that
.. were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
.. to Title 17 United States Code Section 105, works of NIST employees are not
.. subject to copyright protection in the United States. However, NIST may hold
.. international copyright in software created by its employees and domestic
.. copyright (or licensing rights) in portions of software that were assigned or
.. licensed to NIST. To the extent that NIST holds copyright in this software, it is
.. being made available under the Creative Commons Attribution 4.0 International
.. license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
.. of the software developed or licensed by NIST.
..
.. ACCESS THE FULL CC BY 4.0 LICENSE HERE:
.. https://creativecommons.org/licenses/by/4.0/legalcode

.. _dev-guide-merge-request-guidelines:

Merge Request Guidelines
------------------------

.. include:: /_glossary_note.rst

Please follow these steps to submit a contribution using a merge request:

-  Clone the repository to your local computer:

   .. code:: sh

      # Clone with HTTPS
      git clone https://github.com/usnistgov/dioptra.git

      # Clone with SSH
      git clone git@github.com:usnistgov/dioptra.git

-  `Set up a development environment by following the Install instructions in the project README <README.md>`__ and installing the project’s pre-commit hooks:

   .. code:: sh

      pre-commit install --install-hooks
      pre-commit install --hook-type commit-msg

-  Make your changes in a new git branch:

   .. code:: sh

      git checkout -b my-branch master

-  Commit your changes using commit messages that follow the `commit message styleguide <#commit-guidelines>`__:

   .. code:: sh

      # NOTE: the optional commit `-a` option will automatically "add" and "rm" edited files
      git commit -a

   The pre-commit hooks will run a linter that scans your commit message for formatting errors.
   Adherence to these guidelines is required because these commit messages are used to automatically generate the project `CHANGELOG <CHANGELOG.md>`__.

-  Push your branch to GitHub:

   .. code:: sh

      git push origin my-branch

-  In GitHub, open a merge request and set ``my-branch`` as the source branch and ``master`` as the target branch.
   If you need to make changes, you can either push them as additional commits to ``my-branch`` or use ``git rebase`` to amend your initial commits and force push them:

   .. code:: sh

      git rebase master -i
      git push origin my-branch -f

-  Once the contribution has been approved, the project maintainer will rebase ``my-branch`` on the ``master`` branch, generate the updated `CHANGELOG <CHANGELOG.md>`__, and complete the merge.
   Please note that the project maintainer may split, squash, and/or reword some of your commits while preserving your authorship of your code changes.

References
~~~~~~~~~~

-  https://mozillascience.github.io/working-open-workshop/contributing/
-  https://github.com/atom/atom/blob/master/CONTRIBUTING.md
-  https://github.com/angular/angular.js/blob/master/CONTRIBUTING.md
