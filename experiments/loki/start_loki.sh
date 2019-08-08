#!/bin/bash
rm -fr /tmp/loki
rm -fr /tmp/positions.yaml
tmux new -s grafana -d
tmux rename-window -t grafana DBtoJSON
tmux send-keys -t grafana 'python LOLoggerToFile.py' C-m
tmux new-window -t grafana
tmux rename-window -t grafana loki
tmux send-keys -t grafana '$GOPATH/src/github.com/grafana/loki/loki -config.file=./loki-local-config.yaml' C-m
tmux new-window -t grafana
tmux rename-window -t grafana promtail
tmux send-keys -t grafana '$GOPATH/src/github.com/grafana/loki/promtail -config.file=./promtail-local-config.yaml' C-m
tmux attach -t grafana
