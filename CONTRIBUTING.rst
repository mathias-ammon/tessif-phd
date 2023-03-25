============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Bug reports
===========

When `reporting a bug <https://collaborating.tuhh.de/ietma/tessif/-/issues>`_ please include:

    * Your operating system name and version.
    * Any details about your local setup that might be helpful in troubleshooting.
    * Detailed steps to reproduce the bug.

Documentation
=============

Tessif's documentation can always be improved whether its better english, more
concise descriptions or better examples.      

Feature requests and feedback
=============================

The best way to send feedback is to file an issue at https://collaborating.tuhh.de/ietma/tessif/-/issues

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that code contributions are welcome :)

Development
===========

To set up `tessif` for local development:

1. Fork `tessif <https://collaborating.tuhh.de/ietma/tessif>`_
   (look for the "Fork" button).
2. Clone your fork locally::

    git clone https://collaborating.tuhh.de/ietma/tessif.git

3. Create a branch for local development::

    git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

4. When you're done making changes run all the tests with::

    python tests/nose_testing.py

5. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature

6. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code just make the pull request.

For merging, you should:

1. Include passing tests
2. Update documentation when there's new API, functionality etc.
3. Add a note to ``CHANGELOG.rst`` about the changes.
4. Add yourself to ``AUTHORS.rst``.
