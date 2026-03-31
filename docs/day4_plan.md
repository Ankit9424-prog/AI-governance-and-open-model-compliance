## Day 4 objective
Prepare a chunking strategy for parsed documents.
Focus on how chunks should be split and what metadata each chunk should keep.

## First chunking rules
- split by headings/subheadings when possible
- keep paragraphs together when they belong to the same section
- do not mix unrelated sections in one chunk
- keep chunk metadata:
  - doc_id
  - title
  - section_path
  - source_url
  - doc_type
  - jurisdiction

Q. Should i chunk from text file or markdown?
Q. Should heading define chunk boundaries?
Q. What metadata must every chunk carry?