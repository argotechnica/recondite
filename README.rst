Recondite
---------
# Description
Tools for streamlining data reconciliation with Wikidata, focused on efficiency
in gathering data and on streamlining the task of data matching.

Recondite seeks to combine three approaches to helping match and reconcile data
between an offline dataset and Wikidata: (1) search liberally; (2) surface user-
defined information in a visually-coded way to streamline rapid analysis by a
subject matter expert or data analyst; and (3) support iterative analysis with
smart handling of "check status" and "false positive" information.

# Pseudocode describing what Recondite should do:
1. Get user defined list of properties to pull from Wikidata when looking up
entities.

2. Get tidy user data, using a column/combination of columns as search query
input on Wikidata to return items and properties.

3. Output a dataset (or update the existing one?) to show one row for each
result, with properties pulled from Wikidata placed next to data provided in the
input dataset, with a "check" column implemented which clearly shows whether
values in this field match.

# Current state and future plans
Development is still quite early, with lots of the overall workflow still
happening manually. I'm also still new enough to Python that although I'm using
functions, this is not yet a mature library or command-line tool per se. This
would be something to open in your IDE (I'm using Spyder) and work on pseudo-
interactively.

My current use for Recondite is in my work as Wikimedia Data Assistant at the
Bodleian Libraries, University of Oxford, focusing on reconciling relatively
large datasets (thousands of rows) with Wikidata. This explains the current
focus on English only, for example, and the specific parameters that I've
included so far.

TODOs are noted in the code itself, but some larger goals for Recondite include:
- Get Wikidata bot approval so >50 records can be requested at once via API
- Actually document functions
- Write tests
- Package Excel or ODT templates for input/output of data
- Get on Wikidata community pages and maybe PyPi once it's more mature

# References:
[1] https://www.mediawiki.org/wiki/API:Etiquette
[2] https://www.wikidata.org/wiki/Special:ApiHelp/wbgetentities
[3] https://www.wikidata.org/w/api.php?action=help&modules=query
[4] https://www.wikidata.org/wiki/Wikidata:Creating_a_bot
[5] https://python-packaging.readthedocs.io/en/latest/
[6] https://gist.github.com/sloria/7001839
