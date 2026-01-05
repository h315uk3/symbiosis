#!/bin/bash
set -euo pipefail
# Calculate Levenshtein distance between two strings using AWK

# Levenshtein distance implementation in AWK
# Returns the minimum number of edits (insertions, deletions, substitutions)
# needed to transform string1 into string2

levenshtein() {
	local s1="$1"
	local s2="$2"
	
	awk -v s1="$s1" -v s2="$s2" '
	BEGIN {
		n = length(s1)
		m = length(s2)
		
		# Initialize first row and column
		for(i=0; i<=n; i++) d[i,0] = i
		for(j=0; j<=m; j++) d[0,j] = j
		
		# Calculate distances
		for(i=1; i<=n; i++) {
			for(j=1; j<=m; j++) {
				# Cost of substitution
				cost = (substr(s1,i,1) == substr(s2,j,1)) ? 0 : 1
				
				# Minimum of three operations
				deletion = d[i-1,j] + 1
				insertion = d[i,j-1] + 1
				substitution = d[i-1,j-1] + cost
				
				d[i,j] = deletion
				if(insertion < d[i,j]) d[i,j] = insertion
				if(substitution < d[i,j]) d[i,j] = substitution
			}
		}
		
		print d[n,m]
	}'
}

# Main function for standalone usage
if [ "$#" -eq 2 ]; then
	levenshtein "$1" "$2"
fi
