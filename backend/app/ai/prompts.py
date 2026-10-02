SYSTEM = ("You are an evidence-review assistant for grant applications. You never decide legal, compliance or funding eligibility. "
          "Use ONLY the supplied text. Never invent requirements or evidence. Quote evidence verbatim. If unclear, mark ambiguous. "
          "Reply with a single JSON object only, no prose.")
EXTRACT = ('Extract requirements from the guideline. JSON: {{"requirements":[{{"requirement_text":str,"category":"eligibility|submission|documentation|project|budget|timeline|other",'
           '"importance":"mandatory|recommended","ambiguous":bool,"source":{{"document":"{doc}","page":int,"section":str}}}}]}}\n\nGUIDELINE:\n{text}')
MAP = ('For each requirement id, find evidence in the application. status: satisfied|weak|missing|ambiguous|unsupported. evidence must be a verbatim quote; '
       'if none exists use status missing, empty evidence, null source. JSON: {{"mappings":[{{"requirement_id":int,"application_evidence":str,'
       '"application_source":{{"document":"{doc}","page":int,"section":str}}|null,"status":str,"confidence":0..1,"reason":str}}]}}\n\nREQUIREMENTS:\n{reqs}\n\nAPPLICATION:\n{text}')
CLAIMS = ('List factual/impact claims in the application (numbers, outcomes, guarantees) NOT supported by the application\'s own evidence or listed supporting documents. '
          'Say "not supported by supplied evidence", never "false". Quote verbatim. JSON: {{"claims":[{{"claim":str,"source":{{"document":"{doc}","page":int,"section":str}},"note":str}}]}}\n\n'
          'PROVIDED SUPPORTING DOCS: {docs}\n\nAPPLICATION:\n{text}')
QUESTIONS = ('Write concise clarification questions ONLY for these gaps. Each must reference a requirement_id or claim_index. '
             'JSON: {{"questions":[{{"question":str,"requirement_id":int|null,"claim_index":int|null}}]}}\n\nGAPS:\n{gaps}')
