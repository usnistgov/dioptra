<template>
  <q-page class="q-pa-xl bg-grey-2">
    <div class="row justify-center">
      <div class="col-12 col-xl-10">
        
        <div class="q-mb-xl border-bottom">
          <div class="text-h3 text-weight-bold text-blue-grey-9">Dioptra Design System</div>
          <div class="text-subtitle1 text-grey-7 q-mt-sm">
            Inventorying the different components we use for Dioptra and suggesting style guides for them. Articulating a 
            system for emphasizing important elements within tables. 
          </div>
        </div>

        <q-card class="q-mb-xl shadow-1">
          <q-card-section class="q-pa-lg">
            <div class="text-h5 text-primary q-mb-md">1. Emphasizing elements within rows</div>
            <p class="text-body1 text-grey-8">
              We should separate table rows into a handful of components. The main "thing" or identifier of the 
              row should be clearly indicated with bolder, more obvious styling. Background info should fade from
              attention. We can style references to metadata and components to look like they are discrete, 
              attachable objects that were created somewhere else. 
            </p>

            <div class="row q-col-gutter-md q-mt-md">
              <div class="col-12 col-md-4">
                <q-card flat bordered class="bg-grey-1 h-100">
                  <q-card-section>
                    <div class="text-weight-bold text-blue-grey-9">A. The Anchor (main element)</div>
                    <div class="text-caption text-grey-6 q-mb-sm">Name / Entity Title</div>
                    <p class="text-caption">
                      This is what the user is looking for. It should be <strong>Bold</strong> and <strong>Dark</strong>. 
                      It is the primary click target.
                    </p>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-md-4">
                <q-card flat bordered class="bg-grey-1 h-100">
                  <q-card-section>
                    <div class="text-weight-bold text-blue-grey-9">B. The Metadata (Context)</div>
                    <div class="text-caption text-grey-6 q-mb-sm">Description / Dates</div>
                    <p class="text-caption">
                      Secondary information. Should be <code>text-grey-7</code> and smaller. 
                      Truncate if too long using <code>ellipsis</code>.
                    </p>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-md-4">
                <q-card flat bordered class="bg-grey-1 h-100">
                  <q-card-section>
                    <div class="text-weight-bold text-blue-grey-9">C. The Technicals / Attached (Specs)</div>
                    <div class="text-caption text-grey-6 q-mb-sm">IDs / Attached components / Types</div>
                    <p class="text-caption">
                      Machine-readable data. Use <code>Monospace</code> fonts, badges, or pills. 
                      Visually distinct from human text.
                    </p>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </q-card-section>
        </q-card>

        <div class="q-mb-xl">
           <div class="text-h5 text-blue-grey-9 q-mb-md">2. Typography System</div>
           <p class="text-caption">Standardizing styles for different levels of importance</p>
           <q-card class="shadow-1">
             <q-card-section>
               <div class="row q-col-gutter-lg">
                 <div class="col-12 col-md-6">
                   <div class="text-overline text-grey-6">Table Column Headers</div>
                   <div class="q-pa-md bg-grey-1 border-grey">
                      <span class="text-blue-grey-7  text-weight-bold" style="font-size: 0.75rem; letter-spacing: 0.5px">
                        Entity Name
                      </span>
                   </div>
                   <div class="text-caption text-grey-6 q-mt-xs">
                     <code>text-blue-grey-7  text-weight-bold letter-spacing-0-5</code>
                   </div>
                 </div>

                 <div class="col-12 col-md-6">
                   <div class="text-overline text-grey-6">Description / Metadata (Single Line)</div>
                   <div class="q-pa-md bg-grey-1 border-grey">
                      <div class="text-body2 text-grey-7 ellipsis">
                        This is a long description that will be cut off...
                      </div>
                   </div>
                   <div class="text-caption text-grey-6 q-mt-xs">
                     <code>text-body2 text-grey-7 ellipsis</code>
                   </div>
                 </div>

                 <div class="col-12 col-md-6">
                   <div class="text-overline text-grey-6">Primary Entity Anchor</div>
                   <div class="q-pa-md bg-grey-1 border-grey">
                      <div class="text-body2 text-weight-bold text-primary cursor-pointer hover-underline">
                        experiment_alpha_v1
                      </div>
                   </div>
                   <div class="text-caption text-grey-6 q-mt-xs">
                     <code>text-weight-bold text-primary cursor-pointer</code>
                   </div>
                 </div>

                 <div class="col-12 col-md-6">
                   <div class="text-overline text-grey-6">Variable Types</div>
                   <div class="q-pa-md bg-grey-1 border-grey">
                      <span class="font-mono text-caption text-grey-8">dataframe</span>
                   </div>
                   <div class="text-caption text-grey-6 q-mt-xs">
                     <code>font-mono text-caption text-grey-8</code>
                   </div>
                 </div>
               </div>
             </q-card-section>
           </q-card>
        </div>

        <div class="text-h4 q-mb-lg">Exemplar Table Rows</div>

        <div class="text-h5 q-mb-sm text-blue-grey-9">Table Type A: Job Execution</div>
        <div class="text-caption text-grey-7 q-mb-md">
          No main job name to highlight, so lets add an icon to ID and make ID bigger. 
        </div>

        <q-card class="q-mb-xl shadow-2">
          <q-markup-table flat separator="horizontal" class="dioptra-table">
            <thead class="bg-grey-1">
              <tr>
                <th class="text-left" style="width: 80px">Job ID</th>
                <th class="text-left">Description</th>
                <th class="text-left">Entrypoint</th>
                <th class="text-left">Experiment</th>
                <th class="text-left">Queue</th>
                <th class="text-left">Status</th>
                <!-- <th class="text-left">Args</th> -->
                <th class="text-left">Artifacts</th>
                <th class="text-right">Delete</th>
              </tr>
            </thead>
            <tbody>
              <tr class="q-tr--hoverable">
                <td class="vertical-top q-py-md" style="min-width: 100px">
                    <q-btn flat dense no-caps size="md" class="bg-blue-grey-1 text-blue-grey-8 q-px-sm row items-center no-wrap" style="font-family: monospace">
                        <!-- Icon: Added margin-right class (q-mr-xs) -->
                        <q-icon name="outbound" color="indigo-6" size="xs" class="q-mr-xs" />
                        
                        <div class="text-bold">#27</div>
                        
                        <q-tooltip>Go to job: 27</q-tooltip>
                    </q-btn>
                </td>



                <td class="text-left">
                  <div class="text-grey-7 text-caption ellipsis" style="max-width: 200px">
                    hello world test run with extra params
                  </div>
                </td>

                <td class="text-left">
                    <q-badge outline color="orange-8" class="q-pa-xs cursor-pointer">
                      <q-icon name="account_tree" size="xs" class="q-mr-xs" />
                      <span class="font-mono" style="font-size: 12px; font-weight:550">hello_world</span>
                      <q-tooltip>Go to entrypoint: 'hello_world'</q-tooltip>
                    </q-badge>
                </td>

                <td class="text-left">
                    <q-badge outline color="primary" class="q-pa-xs cursor-pointer">
                      <q-icon name="science" size="xs" class="q-mr-xs" />
                      <span class="font-mono" style="font-size: 12px; font-weight:550">hello</span>
                      <q-tooltip>Go to experiment: 'hello'</q-tooltip>
                    </q-badge>
                </td>

                 <td class="text-left">
                    <q-badge outline color="blue-grey-6" class="q-pa-xs  cursor-pointer">
                      <q-icon name="queue" size="xs" class="q-mr-xs" />
                      <span class="font-mono" style="font-size: 12px; font-weight:550">tensorflow-cpu</span>
                      <q-tooltip>Go to queue: 'tensorflow-cpu'</q-tooltip>
                    </q-badge>
                </td>

                <td class="text-left">
                   <q-chip dense outline color="green-7" class="bg-green-1 q-ma-none font-weight-medium">
                      <q-icon name="check_circle" size="xs" class="q-mr-xs" />
                      Finished
                   </q-chip>
                </td>
<!-- 
                <td class="text-left">
                  <div class="bg-grey-2 text-grey-9 q-pa-xs rounded-borders font-mono text-caption" style="display: inline-block; font-size: 11px">
                    no_default_arg=true
                  </div>
                </td> -->

                 <td class="text-left">
                    <q-badge outline color="brown-6" class="q-pa-xs row items-center bg-brown-1 ">
                        <div class="q-mr-sm">
                        <q-icon name="memory" size="xs" />
                        <span style="font-size: 12px">my_greeting.txt</span>
                        </div>
                        <div>
                            <q-btn round flat dense size="xs" color="brown-6" icon="download" class="bg-white" />
                            <q-tooltip>Download "my_greeing.txt"</q-tooltip>
                        </div>
                    </q-badge>
                </td>

                <td class="text-center">
                  <q-btn flat round dense color="negative" icon="delete" size="sm">
                     <q-tooltip>Delete Job</q-tooltip>
                  </q-btn>
                </td>
              </tr>
<tr class="q-tr--hoverable">

                <td class="vertical-top q-py-md" style="min-width: 100px">
                    <q-btn flat dense no-caps size="md" class="bg-blue-grey-1 text-blue-grey-8 q-px-sm row items-center no-wrap" style="font-family: monospace">
                        <!-- Icon: Added margin-right class (q-mr-xs) -->
                        <q-icon name="outbound" color="indigo-6" size="xs" class="q-mr-xs" />
                        
                        <div class="text-bold">#28</div>
                        
                        <q-tooltip>Go to job: 28</q-tooltip>
                    </q-btn>
                </td>

                <td class="text-left">
                  <div class="text-grey-7 text-caption ellipsis" style="max-width: 200px">
                    Same job as above, sans icons
                  </div>
                </td>

                <td class="text-left">
                    <q-badge outline color="orange-8" class="q-pa-sm cursor-pointer">
                      <span class="font-mono" style="font-size: 12px; font-weight:600">hello_world</span>
                      <q-tooltip>Go to entrypoint: 'hello_world'</q-tooltip>
                    </q-badge> 
                </td>

                <td class="text-left">
                    <q-badge outline color="primary" class="q-pa-sm cursor-pointer">
                      <span class="font-mono" style="font-size: 12px; font-weight:600">hello</span>
                      <q-tooltip>Go to experiment: 'hello'</q-tooltip>
                    </q-badge>
                </td>

                 <td class="text-left">
                    <q-badge outline color="blue-grey-6" class="q-pa-sm cursor-pointer">
                      <span class="font-mono" style="font-size: 12px; font-weight:600">tensorflow-cpu</span>
                      <q-tooltip>Go to queue: 'tensorflow-cpu'</q-tooltip>
                    </q-badge>
                </td>

                <td class="text-left">
                   <q-chip dense outline color="green-7" class="bg-green-1 q-ma-none q-py-md font-weight-medium">
                      <q-icon name="check_circle" size="xs" class="q-mr-xs" />
                      Finished
                   </q-chip>
                </td>
<!-- 
                <td class="text-left">
                  <div class="bg-grey-2 text-grey-9 q-pa-xs rounded-borders font-mono text-caption" style="display: inline-block; font-size: 11px">
                    no_default_arg=true
                  </div>
                </td> -->

                 <td class="text-left">
                    <q-badge outline color="brown-6" class="q-pa-sm row items-center bg-brown-1 ">
                        <div class="q-mr-sm">
                        <span style="font-size: 12px">my_greeting.txt</span>
                        </div>
                        <div>
                            <q-btn round flat dense size="xs" color="brown-6" icon="download" class="bg-white" />
                            <q-tooltip>Download "my_greeing.txt"</q-tooltip>
                        </div>
                    </q-badge>
                </td>

                <td class="text-center">
                  <q-btn flat round dense color="negative" icon="delete" size="sm">
                     <q-tooltip>Delete Job</q-tooltip>
                  </q-btn>
                </td>
              </tr>
            </tbody>
          </q-markup-table>
        </q-card>


        <div class="text-h5 q-mb-sm text-blue-grey-9">Table Type B: Entrypoints</div>
        <div class="text-caption text-grey-7 q-mb-md">
          Entrypoint name is the entity name here, so we make it prominently styled and different from how plugin badges are styled.

        </div>

        <q-card class="q-mb-xl shadow-2">
          <q-markup-table flat separator="horizontal" class="dioptra-table">
            <thead class="bg-grey-1">
              <tr>
                <th class="text-left" style="width: 80px">ID</th>
                <th class="text-left" style="width: 180px">Entrypoint Name</th>
                <th class="text-left">Description</th>
                <th class="text-left">Task Graph</th>
                <th class="text-left">Plugins</th>
                <th class="text-left">Artifact Handlers</th>
                <th class="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr class="q-tr--hoverable">
                
                <td class="text-left">
                  <q-btn flat dense no-caps size="sm" class="bg-blue-grey-1 text-blue-grey-8 q-px-sm" style="font-family: monospace">
                    #20
                  </q-btn>
                </td>
                
                <td class="text-left">
                  <div class="row items-center">
                    <q-icon name="account_tree" color="orange-8" size="xs" class="q-mr-sm" />
                    <div class="text-weight-bold text-grey-9 cursor-pointer">Hello World</div>
                  </div>
                </td>
                
                <td class="text-left">
                  <div class="text-grey-7 text-caption ellipsis" style="max-width: 150px">
                    A simple example using the hello_world library
                  </div>
                </td>

                <td class="text-left">
                  <q-btn flat dense no-caps color="primary" size="md" icon="code" label="View YAML" class="bg-blue-1 q-pa-xs" />
                </td>

                <td class="text-left">
                  <div class="row items-center q-gutter-sm justify-center">
                    <div class="column items-left  bg-grey-1 rounded-borders">
                      <div class="column items-left q-my-xs" >
                          <q-badge outline color="teal-7" class="q-pa-xs q-mx-xs">
                              <q-icon name="extension" size="xs" class="q-mr-xs" />
                              <span class="font-mono " style="font-size: 12px; font-weight:550">hello_world</span>
                          </q-badge>
                        <q-badge outline text-color="orange-9" class="q-mx-xs" style="border:none;" >
                          <q-icon name="warning" size="xs" style="font-size:9px"/>
                          v1 (old)
                        </q-badge>

                      </div>
                      <div class=" items-center q-my-xs " >
                          <q-badge outline color="teal-7" class="q-pa-xs  q-mx-xs">
                              <q-icon name="extension" size="xs" class="q-mr-xs" />
                              <span class="font-mono " style="font-size: 12px; font-weight:550">plugin_2</span>
                          </q-badge>
                      </div>
                </div>
                    <q-btn round flat dense size="xs" color="primary" icon="add" class="bg-blue-1" />
                  </div>
                </td>


                <td class="text-left">
                  <div class="row items-center q-gutter-sm justify-center">
                    
                      <div class="column items-left  bg-grey-1 rounded-borders">
                        <div class="column items-left q-my-xs" >
                        <q-badge outline color="teal-7" class="q-pa-xs">
                            <q-icon name="extension" size="xs" class="q-mr-xs" />
                            <span class="font-mono " style="font-size: 12px; font-weight:550">artifact_tasks</span>
                        </q-badge>
                        </div>
                    </div>

                    <q-btn round flat dense size="xs" color="primary" icon="add" class="bg-blue-1" />
                  </div>
                </td>

                <td class="text-center">
                  <q-btn flat round dense color="negative" icon="delete" size="sm" />
                  <q-tooltip>Delete Entrypoint</q-tooltip>
                </td>
              </tr>
            </tbody>
          </q-markup-table>
        </q-card>

<div class="text-h5 q-mb-sm text-blue-grey-9">Table Type C: Function Registry</div>
        <div class="text-caption text-grey-7 q-mb-md">
          Place task name in first column. Maybe we should make an icon for that? New styles for input/output.
          For other input/output options considered, see bottom of page
        </div>

        <q-card class="q-mb-xl shadow-2">
          <q-markup-table flat separator="horizontal" class="dioptra-table">
            <thead class="bg-grey-1">
              <tr>
                <th class="text-left">Function Task</th>
                <th class="text-left">Plugin</th>
                <th class="text-left" style="width: 30%">Input Parameters</th>
                <th class="text-left" style="width: 30%">Output Parameters</th>
                <th class="text-center" style="width: 50px">Add To Task Graph</th>
              </tr>
            </thead>
            <tbody>
              <tr class="q-tr--hoverable ">

                <td class="text-left q-py-md">
                  <div class="text-weight-bold text-primary cursor-pointer hover-underline q-px-sm">greet</div>
                </td>

                <td class="text-left">
                    <q-badge outline color="orange-8" class="q-pa-xs">
                      <q-icon name="account_tree" size="xs" class="q-mr-xs" />
                      <span class="font-mono " style="font-size: 12px; font-weight:550">hello_world</span>
                    </q-badge>
                </td>
            
                
                <td class="vertical-top q-py-md">
                  <div class="column q-gutter-y-sm">
                    
                    <div class="row items-center no-wrap q-gutter-x-sm">
                      <div class="bg-indigo-6 rounded-borders" style="width: 6px; height: 6px"></div>
                      <div class="row items-baseline no-wrap q-gutter-x-sm">
                         <div class="text-weight-bold text-blue-grey-6" style="border-bottom: 1.5px solid #3f51b5; line-height: 1.3">
                           greeting :
                         </div>
                         <div class="font-mono text-weight-medium text-grey-7 cursor-help" style="font-size: 0.75rem">
                           String
                           <q-tooltip content-class="bg-grey-9" content-style="font-size: 11px">A standard UTF-8 string.</q-tooltip>
                         </div>
                      </div>
                    </div>

                    <div class="row items-center no-wrap q-gutter-x-sm">
                      <div class="bg-grey-5 rounded-borders" style="width: 6px; height: 6px"></div>
                      <div class="row items-baseline no-wrap q-gutter-x-sm">
                         <div class="text-weight-bold text-grey-6" style="line-height: 1.3">
                           count :
                         </div>
                         <div class="font-mono text-weight-medium text-grey-7 cursor-help" style="font-size: 0.75rem">
                           Integer
                           <q-tooltip content-class="bg-grey-9" content-style="font-size: 11px">A 32-bit integer value.</q-tooltip>
                         </div>
                         <div class="text-weight-medium text-grey-6" style="font-size: 0.7rem">(optional)</div>
                      </div>
                    </div>

                  </div>
                </td>

                <td class="vertical-top q-py-md">
                   <div class="row items-center no-wrap q-gutter-x-sm">
                      <div class="bg-purple-6 rounded-borders" style="width: 6px; height: 6px"></div>
                      <div class="row items-baseline no-wrap q-gutter-x-sm">
                         <div class="text-weight-bold text-deep-purple-5" style="border-bottom: 1.5px solid #9c27b0; line-height: 1.2">
                           message :
                         </div>
                         <div class="font-mono text-weight-medium text-grey-7 cursor-help" style="font-size: 0.75rem">
                           JSON
                           <q-tooltip content-class="bg-grey-9" content-style="font-size: 11px">A structured JSON object.</q-tooltip>
                         </div>
                      </div>
                   </div>
                </td>

                <td class="text-center q-py-md">
                   <q-btn flat round dense color="grey-7" icon="add" size="sm" class="bg-grey-2" />
                </td>
              </tr>
            </tbody>
          </q-markup-table>
        </q-card>


        <div class="q-mt-xl q-mb-md">
          <div class="text-h5 text-blue-grey-9">3. Iconography Standard</div>
          <div class="text-caption text-grey-7">
            Consistent icon use helps users identify entity types before reading the text.
          </div>
        </div>

        <div class="row q-col-gutter-md q-mb-xl">
          <div class="col-6 col-md-2" v-for="icon in iconMap" :key="icon.name">
            <q-card flat bordered class="text-center q-py-md bg-white">
              <q-icon :name="icon.icon" size="md" :color="icon.color" class="q-mb-sm" />
              <div class="text-caption text-weight-bold text-grey-8">{{ icon.label }}</div>
              <div class="text-xs text-grey-5 font-mono q-pb-sm">{{ icon.icon }}</div>
              <div class="text-xs text-grey-6">{{ icon.color }}</div>
            </q-card>
          </div>
        </div>


        <div class="q-mb-md">
          <div class="text-h5 text-blue-grey-9">4. Component Dictionary</div>
          <div class="text-caption text-grey-7">
            Reusable style definitions. Copy the classes from the "Technical Specs" column.
          </div>
        </div>

        <q-card class="shadow-2 q-mb-xl">
          <q-markup-table flat separator="cell" wrap-cells>
            <thead class="bg-blue-grey-1 text-blue-grey-9">
              <tr>
                <th class="text-left" style="width: 15%">Component Name</th>
                <th class="text-left" style="width: 25%">Visual Preview</th>
                <th class="text-left" style="width: 30%">Design Rationale</th>
                <th class="text-left" style="width: 30%">Technical Specs (Quasar/CSS)</th>
              </tr>
            </thead>
            <tbody>
              
              <tr>
                <td class="text-weight-bold text-grey-9">Input Param</td>
<td class="vertical-top q-py-md">
                  <div class="column q-gutter-y-sm">
                    
                    <div class="row items-center no-wrap q-gutter-x-sm">
                      <div class="bg-indigo-6 rounded-borders" style="width: 6px; height: 6px"></div>
                      <div class="row items-baseline no-wrap q-gutter-x-sm">
                         <div class="text-weight-bold text-blue-grey-6" style="border-bottom: 1.5px solid #3f51b5; line-height: 1.3">
                           greeting :
                         </div>
                         <div class="font-mono text-weight-medium text-grey-7 cursor-help" style="font-size: 0.75rem">
                           String
                           <q-tooltip content-class="bg-grey-9" content-style="font-size: 11px">A standard UTF-8 string.</q-tooltip>
                         </div>
                      </div>
                    </div>

                    <div class="row items-center no-wrap q-gutter-x-sm">
                      <div class="bg-grey-5 rounded-borders" style="width: 6px; height: 6px"></div>
                      <div class="row items-baseline no-wrap q-gutter-x-sm">
                         <div class="text-weight-bold text-grey-6" style="line-height: 1.3">
                           count :
                         </div>
                         <div class="font-mono text-weight-medium text-grey-7 cursor-help" style="font-size: 0.75rem">
                           Integer
                           <q-tooltip content-class="bg-grey-9" content-style="font-size: 11px">A 32-bit integer value.</q-tooltip>
                         </div>
                         <div class="text-weight-medium text-grey-9" style="font-size: 0.7rem">(optional)</div>
                      </div>
                    </div>

                  </div>
                </td>
                <td class="text-caption text-grey-8">
                  For function inputs. Color code blue = input. List like. Differentiate between required and optional. See additional options below
                </td>
                <td>
                  To be determined... see options below
                </td>
              </tr>

               <tr>
                <td class="text-weight-bold text-grey-9">Output Param</td>
                <td class="vertical-top q-py-md">
                   <div class="row items-center no-wrap q-gutter-x-sm">
                      <div class="bg-purple-6 rounded-borders" style="width: 6px; height: 6px"></div>
                      <div class="row items-baseline no-wrap q-gutter-x-sm">
                         <div class="text-weight-bold text-deep-purple-5" style="border-bottom: 1.5px solid #9c27b0; line-height: 1.2">
                           message :
                         </div>
                         <div class="font-mono text-weight-medium text-grey-7 cursor-help" style="font-size: 0.75rem">
                           JSON
                           <q-tooltip content-class="bg-grey-9" content-style="font-size: 11px">A structured JSON object.</q-tooltip>
                         </div>
                      </div>
                   </div>
                </td>
                <td class="text-caption text-grey-8">
                  For function outputs. Purple indicates "Egress/Result".
                </td>
                <td>
                 TBD
                </td>
              </tr>

              <tr>
                <td class="text-weight-bold text-grey-9">Table Header Text</td>
                <td>
                   <span class="text-blue-grey-7  text-weight-bold" style="font-size: 0.75rem; letter-spacing: 0.5px">
                        Column Name
                   </span>
                </td>
                <td class="text-caption text-grey-8">
                   Standardized table headers to be distinct from body text.
                </td>
                <td>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs q-mb-xs">text-blue-grey-7  text-weight-bold</code>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs">letter-spacing: 0.5px</code>
                </td>
              </tr>
              
              <tr>
                <td class="text-weight-bold text-grey-9">Technical ID Pill</td>
                <td>
                  <q-btn flat dense no-caps size="sm" class="bg-blue-grey-1 text-blue-grey-8 q-px-sm" style="font-family: monospace">
                    # a1b2c3
                    <q-tooltip>Copy ID</q-tooltip>
                  </q-btn>
                </td>
                <td class="text-caption text-grey-8">
                  Used for UUIDs. Distinguishes machine data from human names. 
                  Looks clickable (button) to imply "Copy to Clipboard" functionality.
                </td>
                <td>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs q-mb-xs">q-btn (flat, dense, no-caps)</code>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs">class="bg-blue-grey-1 text-blue-grey-8"</code>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs q-mt-xs">font-family: monospace</code>
                </td>
              </tr>

              <tr>
                <td class="text-weight-bold text-grey-9">Secondary Action</td>
                <td>
                  <q-btn flat dense no-caps color="primary" size="md" icon="code" label="View YAML" class="bg-blue-1 q-px-sm" />
                </td>
                <td class="text-caption text-grey-8">
                  For actions like "View Source" or "Download". 
                  Uses a light background (Ghost style) so it doesn't compete with the primary Call to Action (if any).
                </td>
                <td>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs">q-btn (flat, dense, no-caps)</code>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs q-mt-xs">class="bg-blue-1 text-primary"</code>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs q-mt-xs">size="sm"</code>
                </td>
              </tr>

              <tr>
                <td class="text-weight-bold text-grey-9">Resource Badge</td>
                <td>
                    <q-badge outline color="brown-5" class="q-pa-xs">
                      <q-icon name="queue" size="xs" class="q-mr-xs" />
                      <span class="font-mono " style="font-size: 10px">tensorflow-cpu</span>
                    </q-badge>
                </td>
                <td class="text-caption text-grey-8">
                  For Queues, Hardware, or Locations. 
                  Uses "Outline" style to look technical and distinct from colorful status chips.
                </td>
                <td>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs">q-badge (outline)</code>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs q-mt-xs">color="grey-6"</code>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs q-mt-xs">Internal: Icon + Monospace Text</code>
                </td>
              </tr>

              <tr>
                <td class="text-weight-bold text-grey-9">Arg / Code Snippet</td>
                <td>
                  <div class="bg-grey-2 text-grey-9 q-pa-xs rounded-borders font-mono text-caption" style="display: inline-block; font-size: 11px">
                    --lr=0.01
                  </div>
                </td>
                <td class="text-caption text-grey-8">
                  For CLI arguments or configuration snippets. 
                  Mimics a terminal background.
                </td>
                <td>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs">div / span</code>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs q-mt-xs">class="bg-grey-2 text-grey-9 font-mono"</code>
                </td>
              </tr>

              <tr>
                <td class="text-weight-bold text-grey-9">Rich Object Item</td>
                <td>
                    <div class="bg-grey-1 row items-center q-pa-xs rounded-borders" style="border: 1px solid #e0e0e0; width: fit-content">
                       <q-icon name="extension" color="teal-7" size="xs" class="q-mr-xs" />
                       <span class="text-caption text-teal-9 text-weight-medium">plugin_v1</span>
                    </div>
                </td>
                <td class="text-caption text-grey-8">
                  For items in a list (Plugins, Artifacts). 
                  Uses a border to define the object boundary, making it distinct from a simple text list.
                </td>
                <td>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs">border: 1px solid #e0e0e0</code>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs q-mt-xs">class="bg-grey-1 rounded-borders"</code>
                </td>
              </tr>

              <tr>
                <td class="text-weight-bold text-grey-9">Status Chip</td>
                <td>
                   <q-chip dense outline color="green-7" class="bg-green-1 q-ma-none font-weight-medium">
                      <q-icon name="check_circle" size="xs" class="q-mr-xs" />
                      Finished
                   </q-chip>
                </td>
                <td class="text-caption text-grey-8">
                  High visibility system status. 
                  Uses `q-chip` (rounded) instead of badge (square) to indicate a "state of being".
                </td>
                <td>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs">q-chip (dense, outline)</code>
                  <code class="block bg-grey-2 q-pa-xs rounded-borders text-xs q-mt-xs">class="bg-[color]-1"</code>
                </td>
              </tr>

            </tbody>
          </q-markup-table>
        </q-card>
      </div>
    </div>

<div class="row justify-center">
      <div class="col-12 col-xl-10">
        
        <div class="text-h4 text-blue-grey-9 q-mb-md">Alternative Parameter Design Options</div>

        <q-card class="shadow-2">
          <q-markup-table flat separator="cell">
            <thead class="bg-blue-grey-1">
              <tr>
                <th class="text-left" style="width: 20%">Style Name</th>
                <th class="text-left" style="width: 40%">Input Parameters (Indigo)</th>
                <th class="text-left" style="width: 40%">Output Parameters (Purple)</th>
              </tr>
            </thead>
            <tbody>

              <tr>
                <td class="vertical-top q-py-md">
                  <div class="text-weight-bold text-grey-9">Option 1: Variable Block</div>
                </td>
                
                <td class="vertical-top q-py-md">
                  <div class="column q-gutter-y-sm">
                    <div class="row items-center no-wrap">
                      <div class="bg-indigo-1 text-indigo-9 q-px-sm q-py-xs rounded-borders text-weight-bold q-mr-sm" style="font-size: 0.8rem">
                        greeting
                      </div>
                      <div class="column">
                        <span class="font-mono text-grey-6" style="font-size: 0.75rem">String</span>
                        <span class="text-grey-5" style="font-size: 0.65rem; line-height: 1">Required</span>
                      </div>
                    </div>

                    <div class="row items-center no-wrap">
                      <div class="bg-indigo-1 text-indigo-9 q-px-sm q-py-xs rounded-borders text-weight-bold q-mr-sm" style="font-size: 0.8rem">
                        count
                      </div>
                      <div class="column">
                         <span class="font-mono text-grey-6" style="font-size: 0.75rem">Integer</span>
                         <span class="text-grey-5" style="font-size: 0.65rem; line-height: 1">Optional</span>
                      </div>
                    </div>
                  </div>
                </td>

                <td class="vertical-top q-py-md">
                   <div class="row items-center no-wrap">
                      <div class="bg-purple-1 text-purple-9 q-px-sm q-py-xs rounded-borders text-weight-bold q-mr-sm" style="font-size: 0.8rem">
                        message
                      </div>
                      <span class="font-mono text-grey-6" style="font-size: 0.75rem">JSON</span>
                   </div>
                </td>
              </tr>

              <tr>
                <td class="vertical-top q-py-md">
                  <div class="text-weight-bold text-grey-9">Option 2: Metadata Stack</div>
                </td>
                
                <td class="vertical-top q-py-md">
                  <div class="row q-gutter-md">
                    <div class="q-pl-sm" style="border-left: 2px solid #e0e0e0">
                       <div class="text-body2 text-weight-bold text-grey-9" style="line-height: 1.1">greeting</div>
                       <div class="row items-center q-mt-xs">
                          <span class="font-mono text-indigo-8 q-mr-xs" style="font-size: 0.7rem">String</span>
                          <span class="text-grey-5" style="font-size: 0.7rem">• Required</span>
                       </div>
                    </div>

                    <div class="q-pl-sm" style="border-left: 2px solid #e0e0e0">
                       <div class="text-body2 text-weight-bold text-grey-9" style="line-height: 1.1">count</div>
                       <div class="row items-center q-mt-xs">
                          <span class="font-mono text-indigo-8 q-mr-xs" style="font-size: 0.7rem">Integer</span>
                          <span class="text-grey-5" style="font-size: 0.7rem">• Optional</span>
                       </div>
                    </div>
                  </div>
                </td>

                 <td class="vertical-top q-py-md">
                   <div class="q-pl-sm" style="border-left: 2px solid #e0e0e0">
                       <div class="text-body2 text-weight-bold text-grey-9" style="line-height: 1.1">message</div>
                       <div class="row items-center q-mt-xs">
                          <span class="font-mono text-purple-8" style="font-size: 0.7rem">JSON</span>
                       </div>
                    </div>
                </td>
              </tr>

              <tr>
                <td class="vertical-top q-py-md">
                  <div class="text-weight-bold text-grey-9">Option 3: Unified Pill</div>
                </td>
                
                <td class="vertical-top q-py-md">
                  <div class="column q-gutter-y-xs">
                    <div class="bg-grey-1 q-px-sm q-py-xs rounded-borders row items-center justify-between" style="border: 1px solid #e0e0e0; max-width: 220px">
                      <div class="row items-center">
                        <div class="bg-indigo-7 rounded-borders q-mr-sm" style="width: 4px; height: 4px"></div> <span class="text-weight-bold text-grey-9 q-mr-sm" style="font-size: 0.8rem">greeting</span>
                        <span class="font-mono text-grey-6" style="font-size: 0.7rem">String</span>
                      </div>
                      <span class="text-grey-5  text-weight-bold" style="font-size: 0.6rem; letter-spacing: 0.5px">Req</span>
                    </div>

                    <div class="bg-grey-1 q-px-sm q-py-xs rounded-borders row items-center justify-between" style="border: 1px solid #e0e0e0; max-width: 220px">
                      <div class="row items-center">
                        <div class="bg-grey-4 rounded-borders q-mr-sm" style="width: 4px; height: 4px"></div>
                        <span class="text-weight-bold text-grey-9 q-mr-sm" style="font-size: 0.8rem">count</span>
                        <span class="font-mono text-grey-6" style="font-size: 0.7rem">Int</span>
                      </div>
                      <span class="text-grey-5  text-weight-bold" style="font-size: 0.6rem; letter-spacing: 0.5px">Opt</span>
                    </div>
                  </div>
                </td>

                <td class="vertical-top q-py-md">
                   <div class="bg-grey-1 q-px-sm q-py-xs rounded-borders row items-center" style="border: 1px solid #e0e0e0; max-width: 220px">
                      <div class="bg-purple-7 rounded-borders q-mr-sm" style="width: 4px; height: 4px"></div>
                      <span class="text-weight-bold text-grey-9 q-mr-sm" style="font-size: 0.8rem">message</span>
                      <span class="font-mono text-grey-6" style="font-size: 0.7rem">JSON</span>
                    </div>
                </td>
              </tr>
<tr>
                <td class="vertical-top q-py-md">
                  <div class="text-weight-bold text-grey-9">Option 4: Minimal Dot & Line</div>
                </td>
                
                <td class="vertical-top q-py-md">
                  <div class="column q-gutter-y-sm">
                    
                    <div class="row items-center no-wrap q-gutter-x-sm">
                      <div class="bg-indigo-6 rounded-borders" style="width: 6px; height: 6px"></div>
                      <div class="row items-baseline no-wrap q-gutter-x-sm">
                         <div class="text-weight-bold text-grey-9" style="border-bottom: 1.5px solid #3f51b5; line-height: 1.3">
                           greeting
                         </div>
                         <div class="font-mono text-weight-medium text-grey-7 cursor-help" style="font-size: 0.75rem">
                           String
                           <q-tooltip content-class="bg-grey-9" content-style="font-size: 11px">A standard UTF-8 string.</q-tooltip>
                         </div>
                      </div>
                    </div>

                    <div class="row items-center no-wrap q-gutter-x-sm">
                      <div class="bg-grey-5 rounded-borders" style="width: 6px; height: 6px"></div>
                      <div class="row items-baseline no-wrap q-gutter-x-sm">
                         <div class="text-weight-bold text-grey-7" style="line-height: 1.3">
                           count
                         </div>
                         <div class="font-mono text-weight-medium text-grey-7 cursor-help" style="font-size: 0.75rem">
                           Integer (opt)
                           <q-tooltip content-class="bg-grey-9" content-style="font-size: 11px">A 32-bit integer value.</q-tooltip>
                         </div>
                      </div>
                    </div>

                  </div>
                </td>

                <td class="vertical-top q-py-md">
                   <div class="row items-center no-wrap q-gutter-x-sm">
                      <div class="bg-purple-6 rounded-borders" style="width: 6px; height: 6px"></div>
                      <div class="row items-baseline no-wrap q-gutter-x-sm">
                         <div class="text-weight-bold text-grey-9" style="border-bottom: 1.5px solid #9c27b0; line-height: 1.2">
                           message
                         </div>
                         <div class="font-mono text-weight-medium text-grey-7 cursor-help" style="font-size: 0.75rem">
                           JSON
                           <q-tooltip content-class="bg-grey-9" content-style="font-size: 11px">A structured JSON object.</q-tooltip>
                         </div>
                      </div>
                   </div>
                </td>
              </tr>
            </tbody>
          </q-markup-table>
        </q-card>
      </div>
    </div>

  </q-page>
</template>

<script>
export default {
  name: 'DesignSystemPreview',
  setup () {
    return {
      iconMap: [
        { name: 'experiment', label: 'Experiment', icon: 'science', color: 'primary' },
        { name: 'entrypoint', label: 'Entrypoint', icon: 'account_tree', color: 'orange-8' },
        { name: 'plugin', label: 'Plugin', icon: 'extension', color: 'teal-7' },
        { name: 'job', label: 'Job / Task', icon: 'outbound', color: 'indigo-6' },
        { name: 'queue', label: 'Queue', icon: 'queue', color: 'blue-grey-6' },
        { name: 'file', label: 'File / Artifact', icon: 'memory', color: 'brown-5' }
      ]
    }
  }
}
</script>

<style scoped>
.font-mono {
  font-family:  'Courier New', monospace, 'Roboto Mono';
}
.border-bottom {
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 24px;
}
.border-grey {
  border: 1px solid #e0e0e0;
}
.hover-underline:hover {
  text-decoration: underline;
}
/* Subtle Hover effect for table rows */
.q-tr--hoverable:hover td {
  background-color: #fafafa;
}
.dioptra-table th {
  font-weight: 600;
  color: #546e7a; /* blue-grey-7 */
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
</style>