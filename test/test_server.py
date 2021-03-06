import subprocess
try:
    import StringIO.StringIO as StringIO
except:
    from io import StringIO
import sys
import os
root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, root_dir)
from fortls.jsonrpc import write_rpc_request, write_rpc_notification, read_rpc_messages

run_command = os.path.join(root_dir, "fortls.py --unbuffered --incrmental_sync")
test_dir = os.path.join(root_dir, "test/test_source")


def run_request(request):
    pid = subprocess.Popen(run_command, shell=True, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    results = pid.communicate(input=request.encode())
    tmp_file = StringIO(results[0].decode())
    results = read_rpc_messages(tmp_file)
    parsed_results = []
    for result in results:
        if "method" in result:
            continue
        parsed_results.append(result['result'])
    errcode = pid.poll()
    return errcode, parsed_results


def test_init():
    def check_return(result_dict):
        # Expected capabilities
        # {
        #     "completionProvider": {
        #         "resolveProvider": false,
        #         "triggerCharacters": ["."]
        #     },
        #     "definitionProvider": true,
        #     "documentSymbolProvider": true,
        #     "hoverProvider": true,
        #     "textDocumentSync": 1
        # }
        #
        assert "capabilities" in result_dict
        assert result_dict["capabilities"]["textDocumentSync"] == 2
        assert result_dict["capabilities"]["definitionProvider"] is True
        assert result_dict["capabilities"]["documentSymbolProvider"] is True
        assert result_dict["capabilities"]["hoverProvider"] is True
        assert result_dict["capabilities"]["hoverProvider"] == 1
        assert result_dict["capabilities"]["completionProvider"]["resolveProvider"] is False
        assert result_dict["capabilities"]["completionProvider"]["triggerCharacters"][0] == "."
    #
    string = write_rpc_request(1, "initialize", {"rootPath": test_dir})
    errcode, results = run_request(string)
    #
    assert errcode == 0
    check_return(results[0])


def test_open():
    string = write_rpc_request(1, "initialize", {"rootPath": test_dir})
    file_path = os.path.join(test_dir, "subdir", "test_free.f90")
    string += write_rpc_notification("textDocument/didOpen", {
        "textDocument": {"uri": file_path}
    })
    errcode, results = run_request(string)
    #
    assert errcode == 0
    assert len(results) == 1


def test_change():
    string = write_rpc_request(1, "initialize", {"rootPath": test_dir})
    file_path = os.path.join(test_dir, "subdir", "test_free.f90")
    string += write_rpc_notification("textDocument/didChange", {
        "textDocument": {"uri": file_path},
        "contentChanges": [{
            "text": "",
            "range": {
                "start": {"line": 6, "character": 0},
                "end": {"line": 22, "character": 0}
            }
        },
        {
            "text": "",
            "range": {
                "start": {"line": 7, "character": 0},
                "end": {"line": 34, "character": 0}
            }
        }]
    })
    string += write_rpc_request(2, "textDocument/documentSymbol", {
        "textDocument": {"uri": file_path}
    })
    errcode, results = run_request(string)
    #
    assert errcode == 0
    assert len(results) == 2
    assert len(results[1]) == 4


def test_symbols():
    def check_return(result_arrary):
        # Expected objects
        objs = [
            ["test_free", 2, 0, 57],
            ["scale_type", 5, 4, 6],
            ["val", 13, 5, 5],
            ["vector", 5, 8, 14],
            ["n", 13, 9, 9],
            ["v", 13, 10, 10],
            ["create", 6, 12, 12],
            ["norm", 12, 13, 13],
            ["scaled_vector", 5, 16, 21],
            ["scale", 13, 17, 17],
            ["set_scale", 6, 19, 19],
            ["norm", 12, 20, 20],
            ["vector_create", 6, 26, 32],
            ["vector_norm", 12, 34, 38],
            ["scaled_vector_set", 6, 40, 44],
            ["scaled_vector_norm", 12, 46, 50],
            ["unscaled_norm", 12, 52, 56]
        ]
        assert len(result_arrary) == len(objs)
        for i, obj in enumerate(objs):
            assert result_arrary[i]["name"] == obj[0]
            assert result_arrary[i]["kind"] == obj[1]
            assert result_arrary[i]["location"]["range"]["start"]["line"] == obj[2]
            assert result_arrary[i]["location"]["range"]["end"]["line"] == obj[3]
    #
    string = write_rpc_request(1, "initialize", {"rootPath": test_dir})
    file_path = os.path.join(test_dir, "subdir", "test_free.f90")
    string += write_rpc_request(2, "textDocument/documentSymbol", {
        "textDocument": {"uri": file_path}
    })
    errcode, results = run_request(string)
    #
    assert errcode == 0
    check_return(results[1])


def test_comp():
    def check_return(result_arrary, checks):
        assert len(result_arrary["items"]) == checks[0]
        if checks[0] > 0:
            assert result_arrary["items"][0]["label"] == checks[1]
    #
    string = write_rpc_request(1, "initialize", {"rootPath": test_dir})
    file_path = os.path.join(test_dir, "test_prog.f08")
    string += write_rpc_request(2, "textDocument/completion", {
        "textDocument": {"uri": file_path},
        "position": {"line": 12, "character": 6}
    })
    string += write_rpc_request(3, "textDocument/completion", {
        "textDocument": {"uri": file_path},
        "position": {"line": 13, "character": 6}
    })
    string += write_rpc_request(4, "textDocument/completion", {
        "textDocument": {"uri": file_path},
        "position": {"line": 18, "character": 7}
    })
    string += write_rpc_request(5, "textDocument/completion", {
        "textDocument": {"uri": file_path},
        "position": {"line": 19, "character": 20}
    })
    string += write_rpc_request(6, "textDocument/completion", {
        "textDocument": {"uri": file_path},
        "position": {"line": 19, "character": 42}
    })
    string += write_rpc_request(7, "textDocument/completion", {
        "textDocument": {"uri": file_path},
        "position": {"line": 21, "character": 26}
    })
    errcode, results = run_request(string)
    #
    assert errcode == 0
    check_return(results[1], [1, "myfun(n,xval)"])
    check_return(results[2], [1, "glob_sub(n,xval,yval)"])
    check_return(results[3], [1, "stretch_vector"])
    check_return(results[4], [6, "scale"])
    check_return(results[5], [2, "n"])
    check_return(results[6], [1, "val"])


def test_def():
    def check_return(result_arrary, checks):
        assert result_arrary["uri"] == checks[2]
        assert result_arrary["range"]["start"]["line"] == checks[0]
        assert result_arrary["range"]["start"]["line"] == checks[1]
    #
    string = write_rpc_request(1, "initialize", {"rootPath": test_dir})
    file_path = os.path.join(test_dir, "test_prog.f08")
    string += write_rpc_request(2, "textDocument/definition", {
        "textDocument": {"uri": file_path},
        "position": {"line": 12, "character": 6}
    })
    string += write_rpc_request(3, "textDocument/definition", {
        "textDocument": {"uri": file_path},
        "position": {"line": 13, "character": 6}
    })
    string += write_rpc_request(4, "textDocument/definition", {
        "textDocument": {"uri": file_path},
        "position": {"line": 18, "character": 7}
    })
    string += write_rpc_request(5, "textDocument/definition", {
        "textDocument": {"uri": file_path},
        "position": {"line": 19, "character": 20}
    })
    string += write_rpc_request(6, "textDocument/definition", {
        "textDocument": {"uri": file_path},
        "position": {"line": 19, "character": 42}
    })
    string += write_rpc_request(7, "textDocument/definition", {
        "textDocument": {"uri": file_path},
        "position": {"line": 21, "character": 26}
    })
    errcode, results = run_request(string)
    #
    assert errcode == 0
    check_return(results[1], [0, 0, "file://" + os.path.join(test_dir, "subdir", "test_fixed.f")])
    check_return(results[2], [20, 20, "file://" + os.path.join(test_dir, "subdir", "test_fixed.f")])
    check_return(results[3], [10, 10, "file://" + os.path.join(test_dir, "test_prog.f08")])
    check_return(results[4], [19, 19, "file://" + os.path.join(test_dir, "subdir", "test_free.f90")])
    check_return(results[5], [13, 13, "file://" + os.path.join(test_dir, "subdir", "test_free.f90")])
    check_return(results[6], [5, 5, "file://" + os.path.join(test_dir, "subdir", "test_free.f90")])
