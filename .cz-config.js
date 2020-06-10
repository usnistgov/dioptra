module.exports = {
  types: [{
      value: "build",
      name: "build: Changes to the build system or external dependencies",
    },
    {
      value: "ci",
      name: "ci: Changes to CI configuration files and scripts",
    },
    {
      value: "chore",
      name: "chore: Miscellaneous changes that do not fall under any of the other types, such as changes to meta information in the repo (owner files, editor config, etc) or licensing",
    },
    {
      value: "docs",
      name: "docs: Documentation only changes"
    },
    {
      value: "feat",
      name: "feat: A new feature"
    },
    {
      value: "fix",
      name: "fix: A bug fix"
    },
    {
      value: "perf",
      name: "perf: A code change that improves performance",
    },
    {
      value: "refactor",
      name: "refactor: A code change that neither fixes a bug nor adds a feature",
    },
    {
      value: "revert",
      name: "revert: A change that reverses the change in earlier commit"
    },
    {
      value: "style",
      name: "style: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)",
    },
    {
      value: "test",
      name: "test: Adding missing tests or correcting existing tests"
    },
  ],

  scopes: [
    "",
    "client",
    "docker",
    "restapi",
    "server"
  ],

  scopeOverrides: {
    docs: [{
        name: ""
      },
      {
        name: "client"
      },
      {
        name: "contributing"
      },
      {
        name: "docker"
      },
      {
        name: "readme"
      },
      {
        name: "restapi"
      },
      {
        name: "server"
      }
    ]
  },

  messages: {
    type: "Select the type of change that you're committing\n",
    scope: "Denote the SCOPE of this change (optional)\n",
    subject: "Write a short, imperative tense description of the change:\n",
    body: 'Provide a longer description of the change (optional). Use "|" to break new line:\n',
    breaking: "List any breaking changes (optional):\n",
    footer: "List any issues closed by this change (optional). E.g.: #31, #34:\n",
    confirmCommit: "Are you sure you want to proceed with the commit above?",
  },

  allowBreakingChanges: ["feat", "fix"],
  allowCustomScopes: false,
  askForBreakingChangeFirst: false,
  breakingPrefix: "BREAKING CHANGE:",
  breaklineChar: "|",
  footerPrefix: "Closes",
  subjectLimit: 70,
  subjectSeparator: ": ",
  typePrefix: "",
  typeSuffix: "",
  upperCaseSubject: false,

  allowTicketNumber: false,
  isTicketNumberRequired: false,
  ticketNumberPrefix: "Issue-",
  ticketNumberRegExp: "\\d{1,5}"
};
