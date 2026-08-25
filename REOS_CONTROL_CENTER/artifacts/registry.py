def register(state, artifact_id, path, version):
    state.setdefault('artifacts', []).append({'id':artifact_id,'path':str(path),'version':version,'status':'REGISTERED'})
