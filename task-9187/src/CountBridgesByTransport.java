import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.SortedMap;
import java.util.TimeZone;
import java.util.TreeMap;

import org.torproject.descriptor.BridgeNetworkStatus;
import org.torproject.descriptor.Descriptor;
import org.torproject.descriptor.DescriptorFile;
import org.torproject.descriptor.DescriptorReader;
import org.torproject.descriptor.DescriptorSourceFactory;
import org.torproject.descriptor.ExtraInfoDescriptor;
import org.torproject.descriptor.NetworkStatusEntry;
import org.torproject.descriptor.ServerDescriptor;

/*
 * Parses sanitized bridge descriptors to count bridges by transport.
 *
 * Usage: download and extract sanitized bridge descriptors to these
 * subdirectories:
 *
 *   in/statuses/            (bridge network statuses)
 *   in/server-descriptors/  (bridge server descriptors)
 *   in/extra-infos/         (bridge extra-info descriptors)
 *
 * Alternatively, if you're too lazy to extract tarballs, just put them in
 * one of the three directories and make symbolic links in the other two.
 * This will take somewhat longer to execute, because we're going through
 * all tarballs three times.
 *
 * Run with a few GB heap space, e.g., java -Xmx4g ...
 *
 * Results will be written to pt-bridges.csv.
 */
public class CountBridgesByTransport {
  public static void main(String[] args) throws Exception {

    System.out.println(new Date().toString() + " Starting.");

    /* Parse extra-info descriptors to get a mapping from "extra-info
     * descriptor identifier" to "list of transports". */
    System.out.println(new Date().toString() + " Parsing extra-info "
        + "descriptors.");
    Map<String, List<String>> extraInfos =
        new HashMap<String, List<String>>();
    DescriptorReader descriptorReader =
        DescriptorSourceFactory.createDescriptorReader();
    descriptorReader.addDirectory(new File("in/extra-infos"));
    Iterator<DescriptorFile> descriptorFiles =
        descriptorReader.readDescriptors();
    while (descriptorFiles.hasNext()) {
      DescriptorFile descriptorFile = descriptorFiles.next();
      if (descriptorFile.getDescriptors() == null) {
        continue;
      }
      for (Descriptor descriptor : descriptorFile.getDescriptors()) {
        if (!(descriptor instanceof ExtraInfoDescriptor)) {
          continue;
        }
        ExtraInfoDescriptor extraInfoDescriptor =
            (ExtraInfoDescriptor) descriptor;
        if (extraInfoDescriptor.getTransports() == null ||
            extraInfoDescriptor.getTransports().isEmpty()) {
          continue;
        }
        String extraInfoDigest = extraInfoDescriptor.getExtraInfoDigest();
        List<String> transports = extraInfoDescriptor.getTransports();
        extraInfos.put(extraInfoDigest, transports);
      }
    }

    /* Parse server descriptors to get a mapping from "server descriptor
     * identifier" to "extra-info descriptor", but store it as "list of
     * transports". */
    System.out.println(new Date().toString() + " Parsing server "
        + "descriptors.");
    Map<String, List<String>> serverDescriptors =
        new HashMap<String, List<String>>();
    descriptorReader = DescriptorSourceFactory.createDescriptorReader();
    descriptorReader.addDirectory(new File("in/server-descriptors"));
    descriptorFiles = descriptorReader.readDescriptors();
    while (descriptorFiles.hasNext()) {
      DescriptorFile descriptorFile = descriptorFiles.next();
      if (descriptorFile.getDescriptors() == null) {
        continue;
      }
      for (Descriptor descriptor : descriptorFile.getDescriptors()) {
        if (!(descriptor instanceof ServerDescriptor)) {
          continue;
        }
        ServerDescriptor serverDescriptor = (ServerDescriptor) descriptor;
        if (serverDescriptor.getExtraInfoDigest() == null) {
          continue;
        }
        String serverDescriptorDigest =
            serverDescriptor.getServerDescriptorDigest();
        String extraInfoDigest = serverDescriptor.getExtraInfoDigest();
        if (extraInfos.containsKey(extraInfoDigest)) {
          List<String> transports = extraInfos.get(extraInfoDigest);
          serverDescriptors.put(serverDescriptorDigest, transports);
        }
      }
    }

    /* Parse statuses, look up server descriptor identifiers and save
     * number of running bridges by transport to disk as result. */
    System.out.println(new Date().toString() + " Parsing statuses.");
    BufferedWriter bw = new BufferedWriter(new FileWriter(
        "pt-bridges.csv"));
    bw.write("published,transport,bridges\n");
    SimpleDateFormat dateTimeFormat = new SimpleDateFormat(
        "yyyy-MM-dd HH:mm:ss");
    dateTimeFormat.setLenient(false);
    dateTimeFormat.setTimeZone(TimeZone.getTimeZone("UTC"));
    descriptorReader = DescriptorSourceFactory.createDescriptorReader();
    descriptorReader.addDirectory(new File("in/statuses"));
    descriptorFiles = descriptorReader.readDescriptors();
    while (descriptorFiles.hasNext()) {
      DescriptorFile descriptorFile = descriptorFiles.next();
      if (descriptorFile.getDescriptors() == null) {
        continue;
      }
      for (Descriptor descriptor : descriptorFile.getDescriptors()) {
        if (!(descriptor instanceof BridgeNetworkStatus)) {
          continue;
        }
        BridgeNetworkStatus status = (BridgeNetworkStatus) descriptor;
        SortedMap<String, Integer> bridgesByTransport =
            new TreeMap<String, Integer>();
        for (NetworkStatusEntry entry :
            status.getStatusEntries().values()) {
          if (!entry.getFlags().contains("Running")) {
            continue;
          }
          if (serverDescriptors.containsKey(entry.getDescriptor())) {
            List<String> transports =
                serverDescriptors.get(entry.getDescriptor());
            for (String transport : transports) {
              if (!bridgesByTransport.containsKey(transport)) {
                bridgesByTransport.put(transport, 0);
              }
              bridgesByTransport.put(transport,
                  bridgesByTransport.get(transport) + 1);
            }
          }
        }
        if (bridgesByTransport.isEmpty()) {
          continue;
        }
        String publishedString = dateTimeFormat.format(
            status.getPublishedMillis());
        for (Map.Entry<String, Integer> e :
            bridgesByTransport.entrySet()) {
          String transport = e.getKey();
          int bridges = e.getValue();
          bw.write(publishedString + "," + transport + "," + bridges
              + "\n");
        }
      }
    }
    bw.close();

    System.out.println(new Date().toString() + " Terminating.");
  }
}
