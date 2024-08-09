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


Dioptra is a software test platform for assessing the trustworthy characteristics of artificial intelligence (AI). Trustworthy AI is: valid and reliable, safe, secure and resilient, accountable and transparent, explainable and interpretable, privacy-enhanced, and fair - with harmful bias managed1. Dioptra supports the Measure function of the NIST AI Risk Management Framework by providing functionality to assess, analyze, and track identified AI risks.

Use Cases
---------

We envision the following primary use cases for Dioptra:

* Model Testing:
   * 1st party - Assess AI models throughout the development lifecycle
   * 2nd party - Assess AI models during acquisition or in an evaluation lab environment
   * 3rd party - Assess AI models during auditing or compliance activities
* Research: Aid trustworthy AI researchers in tracking experiments
* Evaluations and Challenges: Provide a common platform and resources for participants
* Red-Teaming: Expose models and resources to a red team in a controlled environment


Key Properties
--------------

Dioptra strives for the following key properties:

* Reproducible: Dioptra automatically creates snapshots of resources so experiments can be reproduced and validated
* Traceable: The full history of experiments and their inputs are tracked
* Extensible: Support for expanding functionality and importing existing Python packages via a plugin system
* Interoperable: A type system promotes interoperability between plugins
* Modular: New experiments can be composed from modular components in a simple yaml file
* Secure: Dioptra provides user authentication with access controls coming soon
* Interactive: Users can interact with Dioptra via an intuitive web interface
* Shareable and Reusable: Dioptra can be deployed in a multi-tenant environment so users can share and reuse components

Motivation
----------

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

Context
-------

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

Target Audience
---------------

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

Scope
-----

The testbed is specifically focused on adversarial attacks against the ML algorithms themselves and defensive techniques designed to mitigate the attacks.
In that spirit, the testbed presently is not designed to embed ML algorithms into a larger system context.
For instance, an automated checkout system based on classifying images of products would require additional engineering.
Defenses that could be applied to the surrounding system are currently out of scope.
Similarly, the initial focus has been on image classification algorithms due to the prevalence of available information about attacks and defenses against such algorithms.
There is nothing about the architecture that inherently limits the scope to computer vision, and it would be relatively straightforward to include algorithms using different modalities such as speech recognition or natural language processing.

Architecture Overview
---------------------

The testbed is built on a microservices architecture.
It is designed to be deployed across several physical machines but is equally deployable on a local laptop.
The distributed deployment allows the core optimization algorithms to reside on machines with GPUs or other high-powered computational resources, while a local deployment will impose strong computational constraints.

The heart of the architecture is the core testbed Application Programming Interface (:term:`API`) that manages requests and responses with a human user via a reverse proxy.
The backend Data Storage component hosts datasets, registered models, and experiment results and metrics.
As experiment jobs get submitted, the :term:`API` registers them on the Redis queue, which is watched by a worker pool of Docker containers provisioned with all necessary environment dependencies.
These worker containers run the plugins and coordinate job dependencies and record statistics, metrics, and any generated artifacts.

The architecture relies on a modular plugin system to ease the job of programming new combinations of attacks and defenses.
Plugin tasks perform various basic, low-level functions such as loading models, preparing data, and computing metrics.
They also implement atomic portions of attacks and defenses such as generating adversarial examples or pre-processing images before inference.
Entry points are larger functional units that consist of various ways to wire together registered plugins.
This enables users of different levels of experience and expertise to interact with the testbed.

The architecture is built entirely from open-source resources making it easy for others to extend and improve upon.

Assumptions / System Requirements
---------------------------------

Most of the built-in demonstrations in the testbed assume the testbed is deployed on Unix-based operating systems (e.g., Linux, macOS).
Those familiar with the Windows Subsystem for Linux (WSL) should be able to deploy it on Windows, but this mode is not explicitly supported at this time.
Most included demos perform computationally intensive calculations requiring access to significant computational resources such as Graphics Processing Units (GPUs).
The architecture has been tested on a :term:`NVIDIA DGX` server with 4 GPUs.
The demonstrations also rely on publicly available datasets such as :term:`MNIST` handwritten digits, ImageNet, and Fruits360 that are not part of the testbed distribution.
The built-in demonstrations assume that relevant datasets have already been obtained and saved in the testbed's Data Storage container.
