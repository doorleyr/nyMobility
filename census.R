getCensusApi <- function(url, key, vars, region, numeric=TRUE){
  get <- paste(vars, sep='', collapse=',')
  api_call <- paste(url, 
                    'key=', key, 
                    '&get=', get,
                    '&', region,
                    sep='')
  
  dat_raw <- try(readLines(api_call, warn="F"))
  if(class(dat_raw)=='try-error') {
    print(api_call)
    return}
  dat_df <- data.frame()
  
  #split the datastream into a list with each row as an element
  # Thanks to roodmichael on github
  tmp <- strsplit(gsub("[^[:alnum:], _]", '', dat_raw), "\\,")
  #dat_df <- rbind(dat_df, t(sapply(tmp, '[')))
  #names(dat_df) <- sapply(dat_df[1,], as.character)
  #dat_df <- dat_df[-1,]
  dat_df <- as.data.frame(do.call(rbind, tmp[-1]), stringsAsFactors=FALSE)
  names(dat_df) <- tmp[[1]]
  # convert to numeric
  # The fips should stay as character... so how to distinguish fips from data?
  # I think all of the data have numbers in the names, the fips do not
  #  Example: field names of B01001_001E vs state
  if(numeric==TRUE){
    value_cols <- grep("[0-9]", names(dat_df), value=TRUE)
    for(col in value_cols) dat_df[,col] <- as.numeric(as.character(dat_df[,col]))
  }
  return(dat_df)
}

vecToChunk <- function(x, max=50){
  s <- seq_along(x)
  x1 <- split(x, ceiling(s/max))
  return(x1)
}


key = '7a25a7624075d46f112113d33106b6648f42686a'
acs_16_url <- 'https://api.census.gov/data/2016/acs/acs5/profile?'


vars="B01001_001E"
# get a list of all tracts in the study region
region_tract_manhattan <- 'for=tract:*&in=state:36+county:061'
tract_df_manhattan <- getCensusApi(acs_16_url, key=key, vars=vars, region=region_tract_manhattan)
tract_list <- tract_df_manhattan$tract
df <- NULL
# then use this list of tracts and query on the BGs in each one
for(t in tract_list){# For each tract
  #Construct the regions part of the API Call
  region = paste("for=block+group:*&in=state:36+county:061+tract:", t, sep='')
  # Pull data
  temp.df <- getCensusApi(acs_08_12_url, key=key, vars=vars, region=region)
  df <- rbind(df, temp.df)
}
rm(region,temp.df)
head(df)