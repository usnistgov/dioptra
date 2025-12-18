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

.. _explanation-why-use-dioptra:


Why Use Dioptra?
================

Explaining when Dioptra is appropriate to use and what it's value add is. 


Design Principles
================

Explaining design principles of Dioptra. 


Prior Documentation Snippets
----------------------------


.. note:: 
    The following material is from previous document pages. It needs to be refactored. It is included below as a placeholder and for reference. 

**Key Properties**


Dioptra strives for the following key properties:

* Reproducible: Dioptra automatically creates snapshots of resources so experiments can be reproduced and validated
* Traceable: The full history of experiments and their inputs are tracked
* Extensible: Support for expanding functionality and importing existing Python packages via a plugin system
* Interoperable: A type system promotes interoperability between plugins
* Modular: New experiments can be composed from modular components in a simple yaml file
* Secure: Dioptra provides user authentication with access controls coming soon
* Interactive: Users can interact with Dioptra via an intuitive web interface
* Shareable and Reusable: Dioptra can be deployed in a multi-tenant environment so users can share and reuse components 

**Motivation**


Our systems increasingly rely on Machine Learning (ML) algorithms and models to perform essential functions.
As users of these systems, we must implicitly trust that the models are working as designed.
Establishing the trustworthiness of an ML model is especially hard, because the inner workings are essentially opaque to an outside observer.
Ideally the models we rely on would be transparent, free from bias, explainable, and secure.
Research has shown that ML models are vulnerable to a variety of adversarial attacks that cause them to misbehave in ways that provide benefit to the adversary.
This has sparked a competition between defenses attempting to mitigate
attacks and ever novel attacks that defeat the defenses, and this competition poses a growing challenge for securing ML systems.

In this changing landscape it is extremely difficult to develop a principled approach to evaluating the strengths and weaknesses of defenses.
While much work has been done to evaluate techniques within a narrow range of conditions, there is a challenge in developing more robust metrics that account for the diversity of attacks that might be mounted against it.
Questions about the generalizability of an algorithm across a range of attacks or the transferability of a technique across models or datasets must naturally consider the full range of possible conditions.

The National Institute of Standards and Technology (NIST) National
Cybersecurity Center of Excellence (NCCoE) has built an experimentation testbed to begin to address the broader challenge of evaluation for attacks and defenses.
The testbed aims to facilitate security evaluations of ML algorithms under a diverse set of conditions.
To that end, the testbed has a modular design enabling researchers to easily swap in alternative datasets, models, attacks, and defenses.
The result is the ability to advance the metrology needed to ultimately help secure ML-enabled systems.

**Context**


While there are a large variety of types of attacks against ML algorithms, NIST Internal Report 8269 identifies three broad categories: Evasion, Poisoning, and Oracle.
In Evasion attacks, an adversary manipulates the test data (sometimes by altering the physical environment) in order to cause the ML model to misbehave.
Poisoning attacks alter the training data used to create or maintain a model with the intention of causing it to learn incorrect associations.
Oracle attacks attempt to "reverse engineer" a model to learn about details of the training set used to create it, or specific model parameters to replicate the model.

.. figure:: /images/overview-image-attack-examples.png

In the case of image classification, attacks can manifest in many different ways ranging from the addition of noise which is difficult for humans to detect in the training or testing images, to the inclusion of colorful "patches," which are noticeable by a human observer and can be printed and placed in the physical environment to alter the images entering the classifier.

There are an equal variety in the types of defenses researchers have developed to mitigate the effectiveness of attacks.
These types range from altering the training paradigm for generating models to techniques that pre-process test data in an attempt to eliminate any carefully crafted alterations added by an adversary.
Just as with attacks, defenses can be deployed at any stage of the ML development pipeline.
The simplified diagrams of the development pipeline below depict some examples.

.. figure:: /images/overview-attack-interfaces.png
   :figwidth: 49%
.. figure:: /images/overview-defense-interfaces.png
   :figwidth: 49%

The sheer variety of attacks and defenses results in a combinatorial
explosion of possible combinations of attacks, defenses, model architectures, and datasets, which creates a challenge for evaluating the effectiveness of defenses against the full array of attacks it may face.
Dioptra, the NCCoE's machine learning security testbed, addresses this challenge by making it easier for researchers to explore the set of possible combinations.

**Scope**


The testbed is specifically focused on adversarial attacks against the ML algorithms themselves and defensive techniques designed to mitigate the attacks.
In that spirit, the testbed presently is not designed to embed ML algorithms into a larger system context.
For instance, an automated checkout system based on classifying images of products would require additional engineering.
Defenses that could be applied to the surrounding system are currently out of scope.
Similarly, the initial focus has been on image classification algorithms due to the prevalence of available information about attacks and defenses against such algorithms.
There is nothing about the architecture that inherently limits the scope to computer vision, and it would be relatively straightforward to include algorithms using different modalities such as speech recognition or natural language processing.