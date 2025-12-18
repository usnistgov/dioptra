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

.. _explanation-intended-audience:


Intended Audiences
================

Explaining who Dioptra is for. 



Prior Documentation Snippets
----------------------------

.. note:: 
    The following material is from previous document pages. It needs to be refactored. It is included below as a placeholder and for reference. 



**Target Audience**


We envision an audience with a wide variety of familiarity with and expertise in machine learning.
Newcomers to the platform will be able to run the included demonstrations of attacks and defenses even if they have very little programming experience.

The testbed offers new opportunities for analysts in organizations using ML-enabled products.
For example, the inclusion of testing as part of the build pipeline for first-party developers would help promote more robust products.
Similarly, second-party consumers of such products might leverage the testbed as part of a verification or risk assessment process.
In both cases, the testbed allows users to test a product against a range of attacks, thereby helping them understand what types of threats are most harmful.

We also envision Dioptra as an asset to ML researchers in developing new solutions.
The testbed will allow them to evaluate the security of any new techniques they develop by running those techniques through their paces.
For example, we envision new defenses being tested against a wider array of attacks than is typically found in the literature.
Similarly, it can facilitate "parameter sweeping" to help developers better understand the degree to which small changes in parameters can affect an algorithm.
It also affords an opportunity to replicate and benchmark well-known results from the research literature.
This ability to repeat experiments to reproduce results is critical for creating and validating reliable metrics.

We envision four primary user levels.

Level 1—The Newcomer
   These individuals have little or no hands-on experience with the testbed.
   They will be able to read the documentation and run the provided demos to learn how to use the testbed.
   They will be able to alter the parameters of the provided demos to create slight variants of the existing experiments.
   These users can have a wide variety of skill sets.
   They need not be familiar with the technologies the testbed uses, nor do they have to have much experience with scripting or programming.

Level 2—The Analyst
   These are individuals who want to analyze a wider variety of scenarios.
   They will be able to interface with the testbed's :term:`REST` (**RE**\ presentational **S**\ tate **T**\ ransfer) :term:`API` to create new experiments from existing entry points.
   They will also learn to create custom entry points from the built-in plugins.
   They must know how to customize the testbed's code templates; thus a basic knowledge of scripting or programming is required.

Level 3—The Researcher
   These are individuals who want to run experiments using novel metrics, algorithms, and analytical techniques.
   They will be able to implement their own "in-house" plugins and Software Development Kit (:term:`SDK`) plugins to create novel entry points that rely on custom algorithms.
   They will need to understand the testbed's plugin architecture to extend it with new functionality.
   They, therefore, require a solid background in scripting or programming.

Level 4—The Developer
   These are individuals who want to expand the testbed's core capabilities by contributing to the distribution.
   They will add new features by implementing built-in plugins, :term:`REST` :term:`API` endpoints, :term:`SDK` modules, and architecture extensions.
   These individuals will have a deep understanding of how the testbed's architectural and software components work together.
   They will be able to write reusable code and program applications that conform to coding best practices.