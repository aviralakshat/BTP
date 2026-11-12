# Analyst

The Analyst tab answers from the plant model. It does not call a language-model API.

A question selects one tool in `src/agent/tools.py`. The sentence is built from that tool's fields. `src/agent/grounding.py` then checks every number in the sentence. A number has to sit on a value the tool returned, or on a number the question already contained. Rounding is allowed, including a fraction written as a percent. A sentence that fails the check is withheld.

The tools are read-only. They do not open `parameters.json` or `validation_targets.json` for writing. A request to edit a parameter, or to invent a citation, is refused. Metallisation is reported as an input. Domestic coal is reported as Dey's analysis diluted to higher ash. The axial kiln is reported as geometry plus a prescribed discharge metallisation. Equity NPV, IRR and payback are the waste-heat cash flow after debt service. The tornado and the Monte Carlo stay on the Uncertainty tab, because this chat does not recompute them.

A session holds 12 questions. Each answer has a "Show calculation" view of the tool call.

`src/agent/prompts.py` is the instruction a later API caller would be given. The dashboard does not send it anywhere. Connecting a model means a key in Streamlit secrets and a caller that still has to pass the grounding check. No provider is chosen. That remains open question 3 in `docs/project/OPEN_QUESTIONS.md`.

The questions in `project/tests/agent_evals/cases.json` name the tool and a phrase. They do not name the expected figure. The test runs the model and rejects an answer whose numbers are not in the tool result.

The Summary tab downloads a workbook and a one-page HTML brief. Both are filled from the run on screen and stamped with the model version and the parameter-file hash. The HTML brief is the page to print. The Compare tab places the sidebar next to imported coal and domestic coal, and downloads the sidebar as a scenario file.
