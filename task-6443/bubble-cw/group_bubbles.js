var diameter = 800,
    format = d3.format(",d"),
    color = d3.scale.category20c();

var bubble = d3.layout.pack()
    .sort(null)
    .size([diameter, diameter])
    .padding(1.5);

var svg = d3.select("body").append("svg")
    .attr("width", diameter)
    .attr("height", diameter)
    .attr("class", "bubble");

svg.append("defs")
  .append("filter")
    .attr("id", "middle-filter")
    .append("feColorMatrix")
      .attr("type", "hueRotate")
      .attr("in", "SourceGraphic")
      .attr("values", "90");

d3.json("details.json", function(error, data) {
  var group = {};
  data.relays.forEach(function(relay) {
    if (relay.running) {
      if (typeof exits_only !== 'undefined' && exits_only && relay["exit_probability"] == 0) {
          return;
      }
      if (!group.hasOwnProperty(get_group_id(relay))) {
        group[get_group_id(relay)] = { name: get_group_name(relay), children: [] };
      }
      group[get_group_id(relay)].children.push(
          { name: relay.nickname ? relay.fingerprint : relay.nickname,
            value: relay.consensus_weight,
            exit: relay["exit_probability"] > 0,
            bandwidth: relay["advertised_bandwidth"],
          });
    }
  });

  var cutOff = 100 / 8.0 * 1000.0 * 1000.0; // 100 Mbit/s
  var bubbles = svg.selectAll(".node")
      .data(bubble.nodes({ children: d3.values(group) }));
  var node = bubbles.enter().append("g")
      .attr("class", "node")
      .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });

  node.append("circle")
      .filter(function(d) { return d.children && d.name; })
      .attr("r", function(d) { return d.r; })
      .style("fill", "#888888")
      .style("fill-opacity", ".25");

  node.filter(function(d) { return !d.children && d.r > 1;})
    .append("image")
      .attr("xlink:href", function(d) { return "tor-consensus-vis-node-" + (d.bandwidth > cutOff ? "onion" : "circle") + ".svg"; })
      .attr("transform", function(d) { return "translate(" + -d.r + "," + -d.r + ")"; })
      .attr("width", function(d) { return d.r * 2; })
      .attr("height", function(d) { return d.r * 2; })
      .attr("preserveAspectRatio", "xMidYMin")
      .attr("filter", function(d) { return d.exit ? "" : "url(#middle-filter)"; });

  node.filter(function(d) { return d.children && d.name; })
    .each(function(d) {
      var g = svg.append("g")
        .attr("transform", "translate(" + d.x + "," + d.y + ")");
      g.append("circle")
        .attr("r", d.r)
        .style("fill", "#000000")
        .style("fill-opacity", "0")
        .style("stroke", "none");
      g.on("mouseover", function() {
            svg.append("text")
                .attr("transform", "translate(" + d.x + "," + (d.y - d.r) + ")")
                .attr("id", "group-name")
                .style("text-anchor", "middle")
                .style("font-size", "14pt")
                .text((d.name + "").substring(0, 50));
          })
       .on("mouseout", function() {
            d3.select("#group-name").remove();
          });
    });

  var title = svg.append("g")
      .attr("transform", "translate(" + (diameter / 3) +", " + (diameter - 30) + ")");
  title.append("text")
      .text(graph_title)
      .attr("text-anchor", "middle")
      .attr("style", "font-size: 18pt");
  title.append("text")
      .text(data['relays_published'])
      .attr("text-anchor", "middle")
      .attr("dy", "15")
      .attr("style", "font-size: 10pt");

  var legendWidth = 270;
  var legendHeight = 115;
  var legendIconSize = 50;
  var legendIconMargin = (legendHeight - legendIconSize * 2) / 3;
  var legend = svg.append("g")
      .attr("transform", "translate(" + (diameter - legendWidth - 10) +", " + (diameter - legendHeight - 10) + ")")
  legend.append("rect")
      .attr("width", legendWidth)
      .attr("height", legendHeight)
      .attr("fill", "#cccccc")
      .attr("stroke", "#000000");
  var legendOnion = legend.append("g")
      .attr("transform", "translate(0, " + legendIconMargin + ")");
  legendOnion.append("image")
    .attr("xlink:href", "tor-consensus-vis-node-onion.svg")
      .attr("width", legendIconSize)
      .attr("height", legendIconSize)
      .attr("preserveAspectRatio", "xMidYMin");
  legendOnion.append("text")
      .text("relays with at least " + (cutOff * 8 / 1000 / 1000) + " Mbit/s of capacity")
      .attr("text-anchor", "start")
      .attr("dx", legendIconSize)
      .attr("dy", legendIconSize / 2)
  var legendCircle = legend.append("g")
      .attr("transform", "translate(0, " + (legendIconSize + legendIconMargin * 2) + ")");
  legendCircle.append("image")
    .attr("xlink:href", "tor-consensus-vis-node-circle.svg")
      .attr("width", legendIconSize)
      .attr("height", legendIconSize)
      .attr("preserveAspectRatio", "xMidYMin");
  legendCircle.append("text")
      .text("smaller relays")
      .attr("text-anchor", "start")
      .attr("dx", legendIconSize)
      .attr("dy", legendIconSize / 2)
});

d3.select(self.frameElement).style("height", diameter + "px");

