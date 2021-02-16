.. _dev-guide-merge-request-guidelines:

Merge Request Guidelines
------------------------

Please follow these steps to submit a contribution using a merge request:

-  Clone the repository to your local computer:

   .. code:: sh

      # Clone with HTTPS
      git clone https://gitlab.mitre.org/secure-ai/securing-ai-lab-components.git

      # Clone with SSH
      git clone git@gitlab.mitre.org:secure-ai/securing-ai-lab-components.git

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

-  Push your branch to GitLab:

   .. code:: sh

      git push origin my-branch

-  In GitLab, open a merge request and set ``my-branch`` as the source branch and ``master`` as the target branch.
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
