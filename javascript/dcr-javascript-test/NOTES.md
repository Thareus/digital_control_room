# Digital Control Room - Javascript Test Notes

To Run:
- Avoid opening index.html in the web browser. As this will result in a cross-origin error. Instead, from within the directory containing index.html, run python -m http.server.

## Exercise 1 - Form and chart
- The selection is based on a combination of two radio buttons representing Country and Region and a dropdown for the options for each of those.
- Included an event listener to update the radio selection when the user selects an option in the dropdown menu.
- The table and chart both depend on the updateVisualisation function. 
- The updateVisualisation function prepares the data based on the selected dataType and option via the processCountryData or processRegionData functions. It then calls the updateChart, updateChartHighlightOptions and updateTable functions with this data.

## Exercise 2 - Display as a table
- The updateTable function constructs the table including a header row for indicating which data and adds a row for each item in the data array.

## Exercise 3 - Display as a Bubble Chart
- The updateChart function plots the data as a bubble chart using the D3.js library.
- We are specifically using the 'pack' layout of D3.js to create the bubble chart. This layout is typically used to visualise hierarchies, but achieves the visual effect we want as the data we have is flat.
- The data is sorted by value to achieve a visual effect of largest values in the center, and smaller values on the periphery.
- The size of the bubble reflects the relative value of the data point, so the largest bubbles appear in the center.
- The labels for each bubble are constructed using the item name and first before they are filtered based on whether they will fit inside the bubble. This is to be able to accommodate large country names such as "United Kingdom of Great Britain and Northern Ireland".
- Because of the disparity in values, a dropdown is available to highlight specific options. For instance, in the case of population size, the largest bubbles such as China and India dwarf the sizes of less-populated countries such as Luxembourg. As a side effect, the labels of these countries are not visible. To remedy this situation, the dropdown allows the user to find specific countries and highlight them in the chart.
- When the user hovers over a bubble, a tooltip is displayed with extended information related to the selected option.
