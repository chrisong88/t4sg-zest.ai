// Import pre-existing react libraries
import React, { useEffect, useState } from 'react';
import axios from 'axios';

// Import stylesheet
import 'bootstrap/dist/css/bootstrap.css';
import './style/App.css';

// Import different components
import Description from './components/Description'
import Footer from './components/Footer'
import MainNavBar from './components/MainNavBar'
import BarGraph from './components/BarGraph'
import Button from 'react-bootstrap/Button';

function App() {

  const [loading, setLoading] = useState(false);

  // bisgData stores probabilities from bisg
  var [bisgData, setbisgData] = useState('default bisg');

  // zrpData stores probabilities from zrp model
  var [zrpData, setZrpData] = useState('default zrp');
  var [validAddress, setValidAddress] = useState(false);
  var [address, setAddress] = useState('empty');

  // All input values
  const [allValues, setAllValues] = useState({
    first_name: '',
    middle_name: '',
    last_name: '',
    gender: '',
    age: '',
    street_address: '',
    city: '',
    state: '',
    zipcode: ''
  });

  // Functions that are called whenever the text input is changed
  function changeHandler(e) {
    setAllValues({ ...allValues, [e.target.name]: e.target.value })
  }

  //Returns validated USPS API Response Object
  function validateAddress() {
    return axios.get(`https://secure.shippingapis.com/ShippingAPI.dll?API=Verify&XML=<AddressValidateRequest USERID="658HARVA0117"><Address ID="0"><Address1>${allValues.street_address}</Address1><Address2/><City>${allValues.city}</City><State>${allValues.state}</State><Zip5>${allValues.zipcode}</Zip5><Zip4/></Address></AddressValidateRequest>`)
      .then(res => {
        setAddress(res.data);
        return res.data
      });
  }

  // Function that called when the submit button is pressed
  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);

    const addressData = await validateAddress();
  
    var isValid = addressData.includes("<Error>") ? false : true;         // Check for invalid responses
    setAddress(addressData);
    setValidAddress(isValid);

    if (isValid) {
      var domParser = new DOMParser();
      var xmlDocument = domParser.parseFromString(addressData, "text/xml");

      setAllValues({
        first_name: allValues.first_name,
        middle_name: allValues.middle_name,
        last_name: allValues.last_name,
        gender: allValues.gender,
        age: allValues.age,
        street_address: xmlDocument.getElementsByTagName("Address2")[0].childNodes[0].nodeValue,
        city: xmlDocument.getElementsByTagName("City")[0].childNodes[0].nodeValue,
        state: xmlDocument.getElementsByTagName("State")[0].childNodes[0].nodeValue,
        zipcode: xmlDocument.getElementsByTagName("Zip5")[0].childNodes[0].nodeValue
      });
      
      axios.get(`http://localhost:5000/surgeo?surname=${allValues.last_name}&zipcode=${allValues.zipcode}`)
      .then(res => {
        setbisgData(res.data);
      });
      await axios.get(`http://localhost:5000/zrp?first_name=${allValues.first_name}&middle_name=${allValues.middle_name}&last_name=${allValues.last_name}&gender=${allValues.gender}&age=${allValues.age}&street_address=${allValues.street_address}&city=${allValues.city}&state=${allValues.state}&zipcode=${allValues.zipcode}`)
        .then(res => {
          setZrpData(res.data);
        });
    }
    setLoading(false);
  }

  return (
    <div className="App">
      <MainNavBar />
      <Description />

      <form onSubmit={handleSubmit}>
        <label> Please enter your information: </label>
        <br /> <br />
        First name: <input type="text" name="first_name" onChange={changeHandler} /> <br /> <br />
        Middle name: <input type="text" name="middle_name" onChange={changeHandler} /> <br /> <br />
        Last name: <input type="text" name="last_name" onChange={changeHandler} /> <br /> <br />
        Gender: 
        <select type="text" name="gender" onChange={changeHandler}>
          <option value="U">U</option>
          <option value="M">M</option>
          <option value="F">F</option>
        </select> <br /> <br />
        Age: <input type="text" name="age" onChange={changeHandler} /> <br /> <br />
        Street address: <input type="text" name="street_address" onChange={changeHandler} /> <br /> <br />
        City: <input type="text" name="city" onChange={changeHandler} /> <br /> <br />
        State:  
        <select type="text" name="state" onChange={changeHandler} >
          <option value="FL">FL</option>
        </select> <br /> <br />
        Zip code: <input type="text" name="zipcode" onChange={changeHandler} /> <br /> <br />
        <Button type="submit" value="Submit">Submit</Button>
      </form>

      <br/>

      {(address!= 'empty' && !loading && !validAddress)
        ? <div> <h3> Please input a valid address. </h3></div>
        : <div> </div>
      }
      {(loading) ? <div> <h3>Loading...</h3> </div> : <div></div>}
      { (bisgData == 'default bisg' || loading || !validAddress)
        ? <div> <h3> </h3> </div>
        : <div className="svg-class"><BarGraph white={bisgData.white[0]} 
          black={bisgData.black[0]} api={bisgData.api[0]} hispanic={bisgData.hispanic[0]} 
          multiple={bisgData.multiple[0]} native={bisgData.native[0]} zrpWhite={zrpData["White"]}
          zrpBlack={zrpData["Black"]} zrpApi={zrpData["Asian Pacific Islander"]} zrpHispanic={zrpData["Hispanic"]}
          zrpMulti={zrpData["Multi"]} zrpNative={zrpData["American Indian"]} /> </div>
      }
      <Footer />
    </div>
  );
}

export default App;