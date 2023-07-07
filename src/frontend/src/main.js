// This Software (Dioptra) is being made available as a public service by the
// National Institute of Standards and Technology (NIST), an Agency of the United
// States Department of Commerce. This software was developed in part by employees of
// NIST and in part by NIST contractors. Copyright in portions of this software that
// were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
// to Title 17 United States Code Section 105, works of NIST employees are not
// subject to copyright protection in the United States. However, NIST may hold
// international copyright in software created by its employees and domestic
// copyright (or licensing rights) in portions of software that were assigned or
// licensed to NIST. To the extent that NIST holds copyright in this software, it is
// being made available under the Creative Commons Attribution 4.0 International
// license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
// of the software developed or licensed by NIST.
//
// ACCESS THE FULL CC BY 4.0 LICENSE HERE:
// https://creativecommons.org/licenses/by/4.0/legalcode
//
// Part of this script is adapted from the work
// https://github.com/jupyter/docker-stacks/blob/6bf5922f5a511b4ff28f23783a716df75b8b8d4b/base-notebook/Dockerfile.
// See copyright below.
//
// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// Redistributions of source code must retain the above copyright notice, this
// list of conditions and the following disclaimer.
//
// Redistributions in binary form must reproduce the above copyright notice, this
// list of conditions and the following disclaimer in the documentation and/or
// other materials provided with the distribution.
//
// Neither the name of the Jupyter Development Team nor the names of its
// contributors may be used to endorse or promote products derived from this
// software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
// FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
// DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
// SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
// CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
// OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import { createApp } from 'vue'
import App from './App.vue'

import './assets/main.css'

createApp(App).mount('#app')
