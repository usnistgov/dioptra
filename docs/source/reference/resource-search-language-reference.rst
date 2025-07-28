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

.. _reference-resource-search-language-reference:

====================================
 Resource Search Language Reference
====================================

This document describes the language used to search for resources when using GET queries.

.. contents::

Overview
========

Dioptra defines a query language used for searching for resources. The language is used when 
submitting GET queries for endpoints, in order to narrow down the resources returned to a 
specific set which matches the specifications of the search parameters.

Features
========


Wildcard ``*``
------------

The ``*`` character can be used as a wildcard to represent an arbitrary number of characters.

Example usage:
    * ``search_term_*`` - will search for all text fields that start with ``search_term_``
    
Note that escaping the character, such as in ``search_term_\*`` will result in a search of all
text fields that exactly match ``search_term_*``.


Wildcard ``?``
------------

The ``?`` character can be used as a wildcard to represent a single character.

Example usage:
    * ``search_term_?`` - will search for all text fields that start with ``search_term_`` and only
    have one additional character.

    * ``search_term_??`` - will search for all text fields that start with ``search_term_`` and have 
    two additional characters.


Quoted Search Terms ``""``
--------------------------

Search terms quoted with ``"`` can contain spaces and other characters.

Example usage:
    * ``"search \"this\", and 'that'"`` - will search for all text fields that exactly
    match ``search "this", and 'that'``


Combining Search Terms ``,``
----------------------------

Search terms can be combined using commas.

Example usage:
    * ``search_term_1, search_terms_*, "search_term_3"`` - will search for all text fields that
    match ``search_term_1``, start with ``search_terms_`` and match ``search_term_3``.


Searching by Field Name ``field:``
--------------------------------

The name of a field, for example ``tag``, ``name``, ``description``, etc. can be used to search
for resources. 

Note that quotation marks should be used to include spaces in a single search term.

Example usage:
    * ``tag:my_search_tag`` - will search the tags of resources of this type for text which exactly matches
    ``my_search_tag``

    * ``name:experiment_1`` - will search the names of resources of this type for text that exactly matches
    ``experiment_1``

    * ``description:*LLM*`` - will search the descriptions of resources of this type for text containing
    ``LLM``

    * ``tag:tag1,tag:tag2`` - will search the tags of resources of this type for text which exactly matches
    ``tag1`` or ``tag2``

    * ``tag:"this is a tag with spaces"`` - will search the tags of resources of this type for text which
    exactly matches ``this is a tag with spaces``

Escaped Characters ``\``
----------------------

The ``\`` character can be used to escape characters mentioned above that should be ignored by the query language.

Example usage: 
    * ``tag:\*`` - will search the tags of resources of this type for text which exactly matches ``*``

    * ``tag\:`` - will search the tags of resources of this type for text which exactly matches ``tag:``