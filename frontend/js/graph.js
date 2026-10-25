
var GRAPH_COLORS = {
  primary: "#4a8a4a",
  loop: "#8a3a3a",
  other: "#8a7a3a",
  edge: "#555",
  loopEdge: "#dc143c"
};

function nodeColor(n) {
  if (n.in_loop) {
    return GRAPH_COLORS.loop;
  }
  if (n.primary) {
    return GRAPH_COLORS.primary;
  }
  return GRAPH_COLORS.other;
}

function renderGraph(containerId, graphData) {
  var box = document.getElementById(containerId);
  box.innerHTML = "";

  if (!graphData || !graphData.nodes || graphData.edges.length === 0) {
    box.innerHTML = '<p class="graph-empty">No outside sites to map for this page.</p>';
    return;
  }

  var width = box.clientWidth || 600;
  var height = 380;

  var nodes = [];
  for (var i = 0; i < graphData.nodes.length; i++) {
    var n = graphData.nodes[i];
    nodes.push({
      id: n.id,
      primary: n.primary,
      in_loop: n.in_loop
    });
  }

  var links = [];
  for (var j = 0; j < graphData.edges.length; j++) {
    var e = graphData.edges[j];
    links.push({
      source: e.source,
      target: e.target,
      in_loop: e.in_loop
    });
  }

  var svg = d3.select(box).append("svg")
    .attr("viewBox", "0 0 " + width + " " + height)
    .attr("class", "graph-svg");

  var defs = svg.append("defs");

  var normalArrow = defs.append("marker")
    .attr("id", "arrow")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 22)
    .attr("refY", 0)
    .attr("markerWidth", 7)
    .attr("markerHeight", 7)
    .attr("orient", "auto");
  normalArrow.append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", GRAPH_COLORS.edge);

  var loopArrow = defs.append("marker")
    .attr("id", "arrow-loop")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 22)
    .attr("refY", 0)
    .attr("markerWidth", 7)
    .attr("markerHeight", 7)
    .attr("orient", "auto");
  loopArrow.append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", GRAPH_COLORS.loopEdge);

  var link = svg.append("g").selectAll("line").data(links).join("line")
    .attr("class", function (d) {
      if (d.in_loop) {
        return "loop-edge";
      }
      return "normal-edge";
    })
    .attr("stroke", function (d) {
      if (d.in_loop) {
        return GRAPH_COLORS.loopEdge;
      }
      return GRAPH_COLORS.edge;
    })
    .attr("stroke-width", function (d) {
      if (d.in_loop) {
        return 3;
      }
      return 1.5;
    })
    .attr("marker-end", function (d) {
      if (d.in_loop) {
        return "url(#arrow-loop)";
      }
      return "url(#arrow)";
    });

  var node = svg.append("g").selectAll("g").data(nodes).join("g")
    .attr("class", "graph-node")
    .call(d3.drag()
      .on("start", function (event, d) {
        if (!event.active) {
          sim.alphaTarget(0.3).restart();
        }
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", function (event, d) {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", function (event, d) {
        if (!event.active) {
          sim.alphaTarget(0);
        }
        d.fx = null;
        d.fy = null;
      }));

  node.append("circle")
    .attr("r", function (d) {
      if (d.id === graphData.root) {
        return 14;
      }
      return 10;
    })
    .attr("fill", nodeColor)
    .attr("stroke", function (d) {
      if (d.id === graphData.root) {
        return "#ffffff";
      }
      return "#111";
    })
    .attr("stroke-width", function (d) {
      if (d.id === graphData.root) {
        return 3;
      }
      return 1.5;
    });

  node.append("text")
    .text(function (d) {
      return d.id;
    })
    .attr("dy", -16)
    .attr("text-anchor", "middle")
    .attr("class", "graph-label");

  node.append("title").text(function (d) {
    var tip = d.id;
    if (d.id === graphData.root) {
      tip = tip + " (the page you analyzed)";
    }
    if (d.primary) {
      tip = tip + " - official source";
    }
    if (d.in_loop) {
      tip = tip + " - part of a circular loop!";
    }
    return tip;
  });

  var sim = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(function (d) {
      return d.id;
    }).distance(110))
    .force("charge", d3.forceManyBody().strength(-350))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(30))
    .on("tick", function () {
      for (var i = 0; i < nodes.length; i++) {
        var d = nodes[i];
        d.x = Math.max(20, Math.min(width - 20, d.x));
        d.y = Math.max(30, Math.min(height - 20, d.y));
      }
      link.attr("x1", function (d) {
        return d.source.x;
      }).attr("y1", function (d) {
        return d.source.y;
      }).attr("x2", function (d) {
        return d.target.x;
      }).attr("y2", function (d) {
        return d.target.y;
      });
      node.attr("transform", function (d) {
        return "translate(" + d.x + "," + d.y + ")";
      });
    });

  var legend = document.createElement("div");
  legend.className = "graph-legend";
  legend.innerHTML =
    '<span><i style="background:' + GRAPH_COLORS.primary + '"></i>Official source</span>' +
    '<span><i style="background:' + GRAPH_COLORS.other + '"></i>Unverified</span>' +
    '<span><i style="background:' + GRAPH_COLORS.loop + '"></i>In a loop</span>';
  box.appendChild(legend);
}

if (typeof window !== "undefined") {
  window.renderGraph = renderGraph;
}