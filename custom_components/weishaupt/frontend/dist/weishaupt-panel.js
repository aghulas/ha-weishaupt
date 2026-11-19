var J=globalThis,X=J.ShadowRoot&&(J.ShadyCSS===void 0||J.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,se=Symbol(),ke=new WeakMap,O=class{constructor(s,t,e){if(this._$cssResult$=!0,e!==se)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=s,this.t=t}get styleSheet(){let s=this.o,t=this.t;if(X&&s===void 0){let e=t!==void 0&&t.length===1;e&&(s=ke.get(t)),s===void 0&&((this.o=s=new CSSStyleSheet).replaceSync(this.cssText),e&&ke.set(t,s))}return s}toString(){return this.cssText}},Ae=a=>new O(typeof a=="string"?a:a+"",void 0,se),j=(a,...s)=>{let t=a.length===1?a[0]:s.reduce((e,r,n)=>e+(i=>{if(i._$cssResult$===!0)return i.cssText;if(typeof i=="number")return i;throw Error("Value passed to 'css' function must be a 'css' function result: "+i+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(r)+a[n+1],a[0]);return new O(t,a,se)},Re=(a,s)=>{if(X)a.adoptedStyleSheets=s.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(let t of s){let e=document.createElement("style"),r=J.litNonce;r!==void 0&&e.setAttribute("nonce",r),e.textContent=t.cssText,a.appendChild(e)}},re=X?a=>a:a=>a instanceof CSSStyleSheet?(s=>{let t="";for(let e of s.cssRules)t+=e.cssText;return Ae(t)})(a):a;var{is:ot,defineProperty:lt,getOwnPropertyDescriptor:dt,getOwnPropertyNames:ct,getOwnPropertySymbols:ut,getPrototypeOf:ht}=Object,G=globalThis,Ee=G.trustedTypes,pt=Ee?Ee.emptyScript:"",_t=G.reactiveElementPolyfillSupport,N=(a,s)=>a,ne={toAttribute(a,s){switch(s){case Boolean:a=a?pt:null;break;case Object:case Array:a=a==null?a:JSON.stringify(a)}return a},fromAttribute(a,s){let t=a;switch(s){case Boolean:t=a!==null;break;case Number:t=a===null?null:Number(a);break;case Object:case Array:try{t=JSON.parse(a)}catch{t=null}}return t}},Te=(a,s)=>!ot(a,s),Se={attribute:!0,type:String,converter:ne,reflect:!1,useDefault:!1,hasChanged:Te};Symbol.metadata??=Symbol("metadata"),G.litPropertyMetadata??=new WeakMap;var x=class extends HTMLElement{static addInitializer(s){this._$Ei(),(this.l??=[]).push(s)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(s,t=Se){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(s)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(s,t),!t.noAccessor){let e=Symbol(),r=this.getPropertyDescriptor(s,e,t);r!==void 0&&lt(this.prototype,s,r)}}static getPropertyDescriptor(s,t,e){let{get:r,set:n}=dt(this.prototype,s)??{get(){return this[t]},set(i){this[t]=i}};return{get:r,set(i){let l=r?.call(this);n?.call(this,i),this.requestUpdate(s,l,e)},configurable:!0,enumerable:!0}}static getPropertyOptions(s){return this.elementProperties.get(s)??Se}static _$Ei(){if(this.hasOwnProperty(N("elementProperties")))return;let s=ht(this);s.finalize(),s.l!==void 0&&(this.l=[...s.l]),this.elementProperties=new Map(s.elementProperties)}static finalize(){if(this.hasOwnProperty(N("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(N("properties"))){let t=this.properties,e=[...ct(t),...ut(t)];for(let r of e)this.createProperty(r,t[r])}let s=this[Symbol.metadata];if(s!==null){let t=litPropertyMetadata.get(s);if(t!==void 0)for(let[e,r]of t)this.elementProperties.set(e,r)}this._$Eh=new Map;for(let[t,e]of this.elementProperties){let r=this._$Eu(t,e);r!==void 0&&this._$Eh.set(r,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(s){let t=[];if(Array.isArray(s)){let e=new Set(s.flat(1/0).reverse());for(let r of e)t.unshift(re(r))}else s!==void 0&&t.push(re(s));return t}static _$Eu(s,t){let e=t.attribute;return e===!1?void 0:typeof e=="string"?e:typeof s=="string"?s.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(s=>this.enableUpdating=s),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(s=>s(this))}addController(s){(this._$EO??=new Set).add(s),this.renderRoot!==void 0&&this.isConnected&&s.hostConnected?.()}removeController(s){this._$EO?.delete(s)}_$E_(){let s=new Map,t=this.constructor.elementProperties;for(let e of t.keys())this.hasOwnProperty(e)&&(s.set(e,this[e]),delete this[e]);s.size>0&&(this._$Ep=s)}createRenderRoot(){let s=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return Re(s,this.constructor.elementStyles),s}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(s=>s.hostConnected?.())}enableUpdating(s){}disconnectedCallback(){this._$EO?.forEach(s=>s.hostDisconnected?.())}attributeChangedCallback(s,t,e){this._$AK(s,e)}_$ET(s,t){let e=this.constructor.elementProperties.get(s),r=this.constructor._$Eu(s,e);if(r!==void 0&&e.reflect===!0){let n=(e.converter?.toAttribute!==void 0?e.converter:ne).toAttribute(t,e.type);this._$Em=s,n==null?this.removeAttribute(r):this.setAttribute(r,n),this._$Em=null}}_$AK(s,t){let e=this.constructor,r=e._$Eh.get(s);if(r!==void 0&&this._$Em!==r){let n=e.getPropertyOptions(r),i=typeof n.converter=="function"?{fromAttribute:n.converter}:n.converter?.fromAttribute!==void 0?n.converter:ne;this._$Em=r;let l=i.fromAttribute(t,n.type);this[r]=l??this._$Ej?.get(r)??l,this._$Em=null}}requestUpdate(s,t,e,r=!1,n){if(s!==void 0){let i=this.constructor;if(r===!1&&(n=this[s]),e??=i.getPropertyOptions(s),!((e.hasChanged??Te)(n,t)||e.useDefault&&e.reflect&&n===this._$Ej?.get(s)&&!this.hasAttribute(i._$Eu(s,e))))return;this.C(s,t,e)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(s,t,{useDefault:e,reflect:r,wrapped:n},i){e&&!(this._$Ej??=new Map).has(s)&&(this._$Ej.set(s,i??t??this[s]),n!==!0||i!==void 0)||(this._$AL.has(s)||(this.hasUpdated||e||(t=void 0),this._$AL.set(s,t)),r===!0&&this._$Em!==s&&(this._$Eq??=new Set).add(s))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}let s=this.scheduleUpdate();return s!=null&&await s,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[r,n]of this._$Ep)this[r]=n;this._$Ep=void 0}let e=this.constructor.elementProperties;if(e.size>0)for(let[r,n]of e){let{wrapped:i}=n,l=this[r];i!==!0||this._$AL.has(r)||l===void 0||this.C(r,void 0,n,l)}}let s=!1,t=this._$AL;try{s=this.shouldUpdate(t),s?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(e){throw s=!1,this._$EM(),e}s&&this._$AE(t)}willUpdate(s){}_$AE(s){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(s)),this.updated(s)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(s){return!0}update(s){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(s){}firstUpdated(s){}};x.elementStyles=[],x.shadowRootOptions={mode:"open"},x[N("elementProperties")]=new Map,x[N("finalized")]=new Map,_t?.({ReactiveElement:x}),(G.reactiveElementVersions??=[]).push("2.1.2");var ue=globalThis,Ce=a=>a,Q=ue.trustedTypes,Me=Q?Q.createPolicy("lit-html",{createHTML:a=>a}):void 0,je="$lit$",R=`lit$${Math.random().toFixed(9).slice(2)}$`,Ne="?"+R,ft=`<${Ne}>`,C=document,U=()=>C.createComment(""),W=a=>a===null||typeof a!="object"&&typeof a!="function",he=Array.isArray,gt=a=>he(a)||typeof a?.[Symbol.iterator]=="function",ie=`[ 	
\f\r]`,L=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,De=/-->/g,Pe=/>/g,S=RegExp(`>|${ie}(?:([^\\s"'>=/]+)(${ie}*=${ie}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),He=/'/g,qe=/"/g,Le=/^(?:script|style|textarea|title)$/i,pe=a=>(s,...t)=>({_$litType$:a,strings:s,values:t}),d=pe(1),Rt=pe(2),Et=pe(3),M=Symbol.for("lit-noChange"),h=Symbol.for("lit-nothing"),Oe=new WeakMap,T=C.createTreeWalker(C,129);function Ue(a,s){if(!he(a)||!a.hasOwnProperty("raw"))throw Error("invalid template strings array");return Me!==void 0?Me.createHTML(s):s}var mt=(a,s)=>{let t=a.length-1,e=[],r,n=s===2?"<svg>":s===3?"<math>":"",i=L;for(let l=0;l<t;l++){let c=a[l],u,_,p=-1,g=0;for(;g<c.length&&(i.lastIndex=g,_=i.exec(c),_!==null);)g=i.lastIndex,i===L?_[1]==="!--"?i=De:_[1]!==void 0?i=Pe:_[2]!==void 0?(Le.test(_[2])&&(r=RegExp("</"+_[2],"g")),i=S):_[3]!==void 0&&(i=S):i===S?_[0]===">"?(i=r??L,p=-1):_[1]===void 0?p=-2:(p=i.lastIndex-_[2].length,u=_[1],i=_[3]===void 0?S:_[3]==='"'?qe:He):i===qe||i===He?i=S:i===De||i===Pe?i=L:(i=S,r=void 0);let m=i===S&&a[l+1].startsWith("/>")?" ":"";n+=i===L?c+ft:p>=0?(e.push(u),c.slice(0,p)+je+c.slice(p)+R+m):c+R+(p===-2?l:m)}return[Ue(a,n+(a[t]||"<?>")+(s===2?"</svg>":s===3?"</math>":"")),e]},I=class a{constructor({strings:s,_$litType$:t},e){let r;this.parts=[];let n=0,i=0,l=s.length-1,c=this.parts,[u,_]=mt(s,t);if(this.el=a.createElement(u,e),T.currentNode=this.el.content,t===2||t===3){let p=this.el.content.firstChild;p.replaceWith(...p.childNodes)}for(;(r=T.nextNode())!==null&&c.length<l;){if(r.nodeType===1){if(r.hasAttributes())for(let p of r.getAttributeNames())if(p.endsWith(je)){let g=_[i++],m=r.getAttribute(p).split(R),v=/([.?@])?(.*)/.exec(g);c.push({type:1,index:n,name:v[2],strings:m,ctor:v[1]==="."?oe:v[1]==="?"?le:v[1]==="@"?de:H}),r.removeAttribute(p)}else p.startsWith(R)&&(c.push({type:6,index:n}),r.removeAttribute(p));if(Le.test(r.tagName)){let p=r.textContent.split(R),g=p.length-1;if(g>0){r.textContent=Q?Q.emptyScript:"";for(let m=0;m<g;m++)r.append(p[m],U()),T.nextNode(),c.push({type:2,index:++n});r.append(p[g],U())}}}else if(r.nodeType===8)if(r.data===Ne)c.push({type:2,index:n});else{let p=-1;for(;(p=r.data.indexOf(R,p+1))!==-1;)c.push({type:7,index:n}),p+=R.length-1}n++}}static createElement(s,t){let e=C.createElement("template");return e.innerHTML=s,e}};function P(a,s,t=a,e){if(s===M)return s;let r=e!==void 0?t._$Co?.[e]:t._$Cl,n=W(s)?void 0:s._$litDirective$;return r?.constructor!==n&&(r?._$AO?.(!1),n===void 0?r=void 0:(r=new n(a),r._$AT(a,t,e)),e!==void 0?(t._$Co??=[])[e]=r:t._$Cl=r),r!==void 0&&(s=P(a,r._$AS(a,s.values),r,e)),s}var ae=class{constructor(s,t){this._$AV=[],this._$AN=void 0,this._$AD=s,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(s){let{el:{content:t},parts:e}=this._$AD,r=(s?.creationScope??C).importNode(t,!0);T.currentNode=r;let n=T.nextNode(),i=0,l=0,c=e[0];for(;c!==void 0;){if(i===c.index){let u;c.type===2?u=new z(n,n.nextSibling,this,s):c.type===1?u=new c.ctor(n,c.name,c.strings,this,s):c.type===6&&(u=new ce(n,this,s)),this._$AV.push(u),c=e[++l]}i!==c?.index&&(n=T.nextNode(),i++)}return T.currentNode=C,r}p(s){let t=0;for(let e of this._$AV)e!==void 0&&(e.strings!==void 0?(e._$AI(s,e,t),t+=e.strings.length-2):e._$AI(s[t])),t++}},z=class a{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(s,t,e,r){this.type=2,this._$AH=h,this._$AN=void 0,this._$AA=s,this._$AB=t,this._$AM=e,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let s=this._$AA.parentNode,t=this._$AM;return t!==void 0&&s?.nodeType===11&&(s=t.parentNode),s}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(s,t=this){s=P(this,s,t),W(s)?s===h||s==null||s===""?(this._$AH!==h&&this._$AR(),this._$AH=h):s!==this._$AH&&s!==M&&this._(s):s._$litType$!==void 0?this.$(s):s.nodeType!==void 0?this.T(s):gt(s)?this.k(s):this._(s)}O(s){return this._$AA.parentNode.insertBefore(s,this._$AB)}T(s){this._$AH!==s&&(this._$AR(),this._$AH=this.O(s))}_(s){this._$AH!==h&&W(this._$AH)?this._$AA.nextSibling.data=s:this.T(C.createTextNode(s)),this._$AH=s}$(s){let{values:t,_$litType$:e}=s,r=typeof e=="number"?this._$AC(s):(e.el===void 0&&(e.el=I.createElement(Ue(e.h,e.h[0]),this.options)),e);if(this._$AH?._$AD===r)this._$AH.p(t);else{let n=new ae(r,this),i=n.u(this.options);n.p(t),this.T(i),this._$AH=n}}_$AC(s){let t=Oe.get(s.strings);return t===void 0&&Oe.set(s.strings,t=new I(s)),t}k(s){he(this._$AH)||(this._$AH=[],this._$AR());let t=this._$AH,e,r=0;for(let n of s)r===t.length?t.push(e=new a(this.O(U()),this.O(U()),this,this.options)):e=t[r],e._$AI(n),r++;r<t.length&&(this._$AR(e&&e._$AB.nextSibling,r),t.length=r)}_$AR(s=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);s!==this._$AB;){let e=Ce(s).nextSibling;Ce(s).remove(),s=e}}setConnected(s){this._$AM===void 0&&(this._$Cv=s,this._$AP?.(s))}},H=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(s,t,e,r,n){this.type=1,this._$AH=h,this._$AN=void 0,this.element=s,this.name=t,this._$AM=r,this.options=n,e.length>2||e[0]!==""||e[1]!==""?(this._$AH=Array(e.length-1).fill(new String),this.strings=e):this._$AH=h}_$AI(s,t=this,e,r){let n=this.strings,i=!1;if(n===void 0)s=P(this,s,t,0),i=!W(s)||s!==this._$AH&&s!==M,i&&(this._$AH=s);else{let l=s,c,u;for(s=n[0],c=0;c<n.length-1;c++)u=P(this,l[e+c],t,c),u===M&&(u=this._$AH[c]),i||=!W(u)||u!==this._$AH[c],u===h?s=h:s!==h&&(s+=(u??"")+n[c+1]),this._$AH[c]=u}i&&!r&&this.j(s)}j(s){s===h?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,s??"")}},oe=class extends H{constructor(){super(...arguments),this.type=3}j(s){this.element[this.name]=s===h?void 0:s}},le=class extends H{constructor(){super(...arguments),this.type=4}j(s){this.element.toggleAttribute(this.name,!!s&&s!==h)}},de=class extends H{constructor(s,t,e,r,n){super(s,t,e,r,n),this.type=5}_$AI(s,t=this){if((s=P(this,s,t,0)??h)===M)return;let e=this._$AH,r=s===h&&e!==h||s.capture!==e.capture||s.once!==e.once||s.passive!==e.passive,n=s!==h&&(e===h||r);r&&this.element.removeEventListener(this.name,this,e),n&&this.element.addEventListener(this.name,this,s),this._$AH=s}handleEvent(s){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,s):this._$AH.handleEvent(s)}},ce=class{constructor(s,t,e){this.element=s,this.type=6,this._$AN=void 0,this._$AM=t,this.options=e}get _$AU(){return this._$AM._$AU}_$AI(s){P(this,s)}};var bt=ue.litHtmlPolyfillSupport;bt?.(I,z),(ue.litHtmlVersions??=[]).push("3.3.3");var We=(a,s,t)=>{let e=t?.renderBefore??s,r=e._$litPart$;if(r===void 0){let n=t?.renderBefore??null;e._$litPart$=r=new z(s.insertBefore(U(),n),n,void 0,t??{})}return r._$AI(a),r};var _e=globalThis,w=class extends x{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let s=super.createRenderRoot();return this.renderOptions.renderBefore??=s.firstChild,s}update(s){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(s),this._$Do=We(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return M}};w._$litElement$=!0,w.finalized=!0,_e.litElementHydrateSupport?.({LitElement:w});var yt=_e.litElementPolyfillSupport;yt?.({LitElement:w});(_e.litElementVersions??=[]).push("4.2.2");var me="-",fe={en:{title:"Weishaupt",installation:"Installation",devices:"Devices",definitions:"Definitions",programs:"Weekly programs",loading:"Loading\u2026",no_installation:"No Weishaupt installation is loaded.",unavailable:"ebusd does not answer: the values shown are the last ones read.",value:"Value",name:"Name",age:"Read",range:"Range",write:"Write",entity:"Entity",open:"Open",comfort:"comfort",regulation:"regulation",read_only:"read only",not_loaded:"not loaded by ebusd",not_listened:"not read: no enabled entity",waiting:"waiting for the first reading",not_available:"not available",seconds_ago:"{n} s ago",minutes_ago:"{n} min ago",hours_ago:"{n} h ago",days_ago:"{n} d ago",passive:"sent by the device",clock_offset:"Clock master",clock_line:"{label}: {text}",clock_ahead:"{n} s ahead",clock_behind:"{n} s behind",clock_on_time:"on time",software:"Software",hardware:"Hardware",address:"Bus address",in_use:"In use",source_bundled:"shipped with the integration",source_file:"file beside the configuration: {file}",refused:"Files not used",mismatches:"Differences with ebusd",named_from_metadata:"Entities named from the definitions",not_named:"Entities waiting for a name",messages:"Messages",usable:"{usable} of {messages} loaded by ebusd as described",writes:"Writes",writes_off:"disabled in the options",switch_on:"switch on",switch_off:"switch off",capability:"run-time checksum: {value}",per_hour:"{n} of {max} this hour",ebusd:"ebusd",unknown_addresses:"Addresses answering that no definition knows",none:"none",day_unread:"not read yet",day_none:"no range",editable:"editable through its program-day entities",not_editable:"read only: not proven writable on this device",not_read_program:"not loaded by ebusd",program_not_listened:"not read by any enabled entity: read it once now, or enable the program sensor to keep it up to date",write_hint:"Change a setting with its button Change (the writes switch must be on). Comfort: written at once and read back; regulation: after a confirmation in this panel. Open shows the entity.",description:"Description",no_sensor:"no sensor",kept:"kept from before the reload, read again soon",through:"through {circuit}",read_now:"Read now",read_cost:"{n} requests to the bus, about {s} s, once",read_queued:"{n} requests queued; the grid fills in as they are answered",readable:"{usable} of {readable} readable messages loaded by ebusd as described",not_usable:"Messages not read",reason_write_only:"write only",reason_device_absent:"device not on the bus",absent_circuit:"{circuit}: {n} messages, device not on the bus",reason_mismatch:"not loaded as described",reason_other:"not read",disabled:"disabled",reloading:"The integration was reloaded: loading again\u2026",read_only_settings:"Settings left read-only",edit:"Change",write_now:"Write",cancel:"Cancel",confirm:"Write to the controller",confirm_clock:"Send the time",confirm_title:"Confirm: {setting} \u2014 {device}",current:"Current value",new_value:"New value",allowed:"Allowed",path:"Written to bus address {address}, register {register}, from source address {source} ({source_text}). Read back right after.",path_short:"bus address {address}, register {register}, from {source}",regulation_note:"This setting changes how the heating is regulated: it is written after your confirmation.",comfort_note:"Comfort setting: written at once and read back.",writing:"Writing\u2026",written_line:"{before} \u2192 {after}{frame}: {result}",not_written:"Not written: {message}",not_offered_writes_disabled:"writes are not enabled in the options",not_offered:"not offered on this installation: {reason}",switch_off_hint:"The writes switch is off: turn it on to write.",edit_days:"Edit",write_days:"Write the changed days",discard:"Discard changes",copy_to:"Copy to",copy:"Copy",cost:"{days} days changed: up to {writes} writes (only changed slots are written); {used} of {max} this hour",cost_one:"1 day changed: up to {writes} writes (only changed slots are written); {used} of {max} this hour",interrupted:"no answer from Home Assistant (connection interrupted): the write may or may not have been sent; check the value read back",drag_hint:"Type the ranges, or drag on the bar to add one in quarters of an hour; a click on a range removes it.",day_format:"use HH:MM-HH:MM, up to three ranges, or -",day_quarter:"times must be quarters of an hour, from 00:00 to 24:00",day_order:"a range must end after it starts",day_too_many:"at most three ranges",day_overlap:"ranges must not overlap",set_clock:"Set the clock",clock_confirm:"Will send Home Assistant's time at second 00 of the next minute ({send_at}), to bus address fe from source address 31. If the bus is not free within {late} s of second 00, nothing is sent.",clock_sent:"Sent {requested} ({frame}): {result}",clock_current:"Clock master now: {current}",col_device:"Device",col_menu:"Menu",col_label:"Setting",col_value:"Value",col_unit:"Unit",col_range:"Range (step) or choices",col_writable:"Writable",report:"Printable report",export_csv:"Export CSV",report_title:"Settings of the installation",report_subtitle:"{date} \xB7 definitions {version} \xB7 read by the Weishaupt integration of Home Assistant",report_no_factory:"Factory values: the definitions do not carry them yet. An empty value was not read when the report was made.",report_blocked:"The browser blocked the report window: allow pop-ups for Home Assistant and try again.",faults:"Faults",fault_history:"Fault history",fault_counters:"Fault counters",fault_log:"Fault log of the system manager (selected entry)",fault_code:"Code",fault_text:"Text",fault_slot:"Slot",fault_values:"Values stored with it",fault_number:"Fault",fault_count:"Count",fault_none:"no fault stored",fault_unordered:"Order unknown: the pointer to the last entry is not read.",fault_no_time:"The boiler stores no time with an entry.",fault_log_fields:"Entry {id}: code {code}, type {type}, origin {device}, {time}",fault_log_hint:"The operating unit of the system manager selects the entry shown; selecting another one is a write, which the panel does not do.",faults_unread:"{n} of these messages are read by no enabled entity.",faults_read_once:"Read once on demand: not kept up to date unless their entities are enabled.",read_nothing:"Nothing to request: these messages are already read by enabled entities or waiting.",card_name:"Weishaupt weekly program",card_description:"The week grid of one weekly program of a Weishaupt controller.",card_no_entity:"Choose a program sensor of the Weishaupt integration in the card's settings.",card_missing:"{entity} does not exist, or is disabled: enable it in Settings \u2192 Entities (program sensors are created disabled).",card_unavailable:"{entity} is unavailable: ebusd or the controller does not answer.",card_unread:"not read yet",card_editor_entity:"Program sensor",card_editor_title:"Title (optional)",card_editor_today:"Mark today",card_edit:"Edit",card_type_hint:"Type up to three ranges a day, HH:MM-HH:MM, or - for none; only changed days are written.",card_edit_admin:"Days are changed by administrators, here or in the Weishaupt panel.",card_not_writable:"This program is not proven writable on its device: read only.",card_writing_day:"{day}: writing\u2026",card_written_day:"{day}: written and read back",card_failed_day:"{day}: not written: {message}",card_no_switch:"Writes are not enabled in the options of the integration.",read_queued_one:"1 request queued (about {s} s).",read_queued_n:"{n} requests queued (about {s} s).",read_after_first_pass:"They come after the first pass that follows a start: {n} reads still due, {wait}.",read_after_queue:"They come after {n} reads already due, {wait}.",about_s:"about {n} s",about_min:"about {n} min"},fr:{title:"Weishaupt",installation:"Installation",devices:"Appareils",definitions:"D\xE9finitions",programs:"Programmes hebdomadaires",loading:"Chargement\u2026",no_installation:"Aucune installation Weishaupt n'est charg\xE9e.",unavailable:"ebusd ne r\xE9pond pas : les valeurs affich\xE9es sont les derni\xE8res lues.",value:"Valeur",name:"Nom",age:"Lu",range:"Plage",write:"\xC9criture",entity:"Entit\xE9",open:"Ouvrir",comfort:"confort",regulation:"r\xE9gulation",read_only:"lecture seule",not_loaded:"non charg\xE9 par ebusd",not_listened:"non lu : aucune entit\xE9 activ\xE9e",waiting:"en attente de la premi\xE8re lecture",not_available:"non disponible",seconds_ago:"il y a {n} s",minutes_ago:"il y a {n} min",hours_ago:"il y a {n} h",days_ago:"il y a {n} j",passive:"envoy\xE9 par l'appareil",clock_offset:"Horloge ma\xEEtresse",clock_line:"{label} : {text}",clock_ahead:"{n} s d'avance",clock_behind:"{n} s de retard",clock_on_time:"\xE0 l'heure",software:"Logiciel",hardware:"Mat\xE9riel",address:"Adresse de bus",in_use:"Utilis\xE9es",source_bundled:"livr\xE9es avec l'int\xE9gration",source_file:"fichier \xE0 c\xF4t\xE9 de la configuration : {file}",refused:"Fichiers non utilis\xE9s",mismatches:"\xC9carts avec ebusd",named_from_metadata:"Entit\xE9s nomm\xE9es par les d\xE9finitions",not_named:"Entit\xE9s en attente d'un nom",messages:"Messages",usable:"{usable} sur {messages} charg\xE9s par ebusd comme d\xE9crits",writes:"\xC9critures",writes_off:"d\xE9sactiv\xE9es dans les options",switch_on:"interrupteur allum\xE9",switch_off:"interrupteur \xE9teint",capability:"checksum \xE0 l'ex\xE9cution : {value}",per_hour:"{n} sur {max} cette heure",ebusd:"ebusd",unknown_addresses:"Adresses qui r\xE9pondent sans d\xE9finition",none:"aucun",day_unread:"pas encore lu",day_none:"aucune plage",editable:"modifiable par ses entit\xE9s de jour de programme",not_editable:"lecture seule : \xE9criture non prouv\xE9e sur cet appareil",not_read_program:"non charg\xE9 par ebusd",program_not_listened:"lu par aucune entit\xE9 activ\xE9e : lisez-le une fois maintenant, ou activez le capteur du programme pour le tenir \xE0 jour",write_hint:"Modifiez un r\xE9glage avec son bouton Modifier (l'interrupteur d'\xE9criture doit \xEAtre allum\xE9). Confort : \xE9crit aussit\xF4t et relu ; r\xE9gulation : apr\xE8s une confirmation dans ce panneau. Ouvrir affiche l'entit\xE9.",description:"Description",no_sensor:"pas de sonde",kept:"conserv\xE9e d'avant le rechargement, relue bient\xF4t",through:"par {circuit}",read_now:"Lire maintenant",read_cost:"{n} requ\xEAtes sur le bus, environ {s} s, une seule fois",read_queued:"{n} requ\xEAtes en file ; la grille se remplit au fil des r\xE9ponses",readable:"{usable} sur {readable} messages lisibles charg\xE9s par ebusd comme d\xE9crits",not_usable:"Messages non lus",reason_write_only:"\xE9criture seule",reason_device_absent:"appareil absent du bus",absent_circuit:"{circuit} : {n} messages, appareil absent du bus",reason_mismatch:"non charg\xE9 comme d\xE9crit",reason_other:"non lu",disabled:"d\xE9sactiv\xE9e",reloading:"L'int\xE9gration a \xE9t\xE9 recharg\xE9e : nouveau chargement\u2026",read_only_settings:"R\xE9glages laiss\xE9s en lecture seule",edit:"Modifier",write_now:"\xC9crire",cancel:"Annuler",confirm:"\xC9crire dans le r\xE9gulateur",confirm_clock:"Envoyer l'heure",confirm_title:"Confirmer : {setting} \u2014 {device}",current:"Valeur actuelle",new_value:"Nouvelle valeur",allowed:"Valeurs autoris\xE9es",path:"\xC9crit \xE0 l'adresse de bus {address}, registre {register}, depuis l'adresse source {source} ({source_text}). Relu juste apr\xE8s.",path_short:"adresse de bus {address}, registre {register}, depuis {source}",regulation_note:"Ce r\xE9glage modifie la r\xE9gulation du chauffage : il est \xE9crit apr\xE8s votre confirmation.",comfort_note:"R\xE9glage de confort : \xE9crit aussit\xF4t et relu.",writing:"\xC9criture\u2026",written_line:"{before} \u2192 {after}{frame} : {result}",not_written:"Non \xE9crit : {message}",not_offered_writes_disabled:"l'\xE9criture n'est pas activ\xE9e dans les options",not_offered:"non propos\xE9 sur cette installation : {reason}",switch_off_hint:"L'interrupteur d'\xE9criture est \xE9teint : allumez-le pour \xE9crire.",edit_days:"Modifier",write_days:"\xC9crire les jours modifi\xE9s",discard:"Abandonner les modifications",copy_to:"Copier vers",copy:"Copier",cost:"{days} jours modifi\xE9s : jusqu'\xE0 {writes} \xE9critures (seuls les cr\xE9neaux chang\xE9s sont \xE9crits) ; {used} sur {max} cette heure",cost_one:"1 jour modifi\xE9 : jusqu'\xE0 {writes} \xE9critures (seuls les cr\xE9neaux chang\xE9s sont \xE9crits) ; {used} sur {max} cette heure",interrupted:"pas de r\xE9ponse de Home Assistant (connexion interrompue) : l'\xE9criture a pu partir ou non ; v\xE9rifiez la valeur relue",drag_hint:"Saisissez les plages, ou glissez sur la barre pour en ajouter une au quart d'heure ; un clic sur une plage la retire.",day_format:"\xE9crivez HH:MM-HH:MM, trois plages au plus, ou -",day_quarter:"les heures doivent \xEAtre des quarts d'heure, de 00:00 \xE0 24:00",day_order:"une plage doit finir apr\xE8s son d\xE9but",day_too_many:"trois plages au plus",day_overlap:"les plages ne doivent pas se chevaucher",set_clock:"Mettre \xE0 l'heure",clock_confirm:"Enverra l'heure de Home Assistant \xE0 la seconde 00 de la minute suivante ({send_at}), \xE0 l'adresse de bus fe depuis l'adresse source 31. Si le bus n'est pas libre dans les {late} s apr\xE8s la seconde 00, rien n'est envoy\xE9.",clock_sent:"Envoy\xE9 {requested} ({frame}) : {result}",clock_current:"Horloge ma\xEEtresse maintenant : {current}",col_device:"Appareil",col_menu:"Menu",col_label:"R\xE9glage",col_value:"Valeur",col_unit:"Unit\xE9",col_range:"Plage (pas) ou choix",col_writable:"Inscriptible",report:"Rapport imprimable",export_csv:"Exporter en CSV",report_title:"R\xE9glages de l'installation",report_subtitle:"{date} \xB7 d\xE9finitions {version} \xB7 lus par l'int\xE9gration Weishaupt de Home Assistant",report_no_factory:"Valeurs d'usine : les d\xE9finitions ne les donnent pas encore. Une valeur vide n'\xE9tait pas lue au moment du rapport.",report_blocked:"Le navigateur a bloqu\xE9 la fen\xEAtre du rapport : autorisez les fen\xEAtres pour Home Assistant et r\xE9essayez.",faults:"D\xE9fauts",fault_history:"M\xE9moire de d\xE9fauts",fault_counters:"Compteurs de d\xE9fauts",fault_log:"Journal de d\xE9fauts du manager syst\xE8me (entr\xE9e s\xE9lectionn\xE9e)",fault_code:"Code",fault_text:"Texte",fault_slot:"Emplacement",fault_values:"Valeurs enregistr\xE9es avec lui",fault_number:"D\xE9faut",fault_count:"Nombre",fault_none:"aucun d\xE9faut enregistr\xE9",fault_unordered:"Ordre inconnu : le pointeur de la derni\xE8re entr\xE9e n'est pas lu.",fault_no_time:"La chaudi\xE8re n'enregistre pas d'heure avec une entr\xE9e.",fault_log_fields:"Entr\xE9e {id} : code {code}, type {type}, origine {device}, {time}",fault_log_hint:"Le tableau de commande du manager syst\xE8me choisit l'entr\xE9e affich\xE9e ; en choisir une autre est une \xE9criture, que le panneau ne fait pas.",faults_unread:"{n} de ces messages ne sont lus par aucune entit\xE9 activ\xE9e.",faults_read_once:"Lus une fois \xE0 la demande : pas tenus \xE0 jour tant que leurs entit\xE9s ne sont pas activ\xE9es.",read_nothing:"Rien \xE0 demander : ces messages sont d\xE9j\xE0 lus par des entit\xE9s activ\xE9es ou en attente.",card_name:"Programme hebdomadaire Weishaupt",card_description:"La grille de la semaine d'un programme hebdomadaire d'un r\xE9gulateur Weishaupt.",card_no_entity:"Choisissez un capteur de programme de l'int\xE9gration Weishaupt dans les r\xE9glages de la carte.",card_missing:"{entity} n'existe pas ou est d\xE9sactiv\xE9 : activez-le dans Param\xE8tres \u2192 Entit\xE9s (les capteurs de programme sont cr\xE9\xE9s d\xE9sactiv\xE9s).",card_unavailable:"{entity} est indisponible : ebusd ou le r\xE9gulateur ne r\xE9pond pas.",card_unread:"pas encore lu",card_editor_entity:"Capteur de programme",card_editor_title:"Titre (facultatif)",card_editor_today:"Marquer aujourd'hui",card_edit:"Modifier",card_type_hint:"Saisissez jusqu'\xE0 trois plages par jour, HH:MM-HH:MM, ou - pour aucune ; seuls les jours modifi\xE9s sont \xE9crits.",card_edit_admin:"Les jours sont modifi\xE9s par les administrateurs, ici ou dans le panneau Weishaupt.",card_not_writable:"Ce programme n'est pas prouv\xE9 inscriptible sur son appareil : lecture seule.",card_writing_day:"{day} : \xE9criture\u2026",card_written_day:"{day} : \xE9crit et relu",card_failed_day:"{day} : non \xE9crit : {message}",card_no_switch:"L'\xE9criture n'est pas activ\xE9e dans les options de l'int\xE9gration.",read_queued_one:"1 requ\xEAte en file (environ {s} s).",read_queued_n:"{n} requ\xEAtes en file (environ {s} s).",read_after_first_pass:"Elles passent apr\xE8s la premi\xE8re lecture qui suit un d\xE9marrage : {n} lectures encore dues, {wait}.",read_after_queue:"Elles passent apr\xE8s {n} lectures d\xE9j\xE0 dues, {wait}.",about_s:"environ {n} s",about_min:"environ {n} min"}},E={en:["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],fr:["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]};function Ve(a){let s=(a??"en").split("-")[0];return s in fe?s:"en"}function o(a,s,t={}){return(fe[a]?.[s]??fe.en[s]??s).replace(/\{(\w+)\}/g,(r,n)=>String(t[n]??`{${n}}`))}function f(a,s){return a?a[s]??a.en??Object.values(a)[0]??"":""}function be(a,s,t){if(!s)return null;let e=s.values[a.index];if(e===void 0)return null;if(e===me)return o(t,"not_available");if(a.absent!==null&&a.absent!==void 0&&Number(e)===a.absent)return o(t,"no_sensor");if(a.values){let r=a.values[e];return r?f(r,t):e}return a.unit?`${e} ${a.unit}`:e}function Be(a,s){let t=e=>e.split(" (")[0].trim().toLowerCase();return!a||t(a)===t(s)}function F(a,s){for(let t of a.messages??[a.message]){let e=s[t];if(e)return e}return null}function Ke(a,s){let t=new Map,e=[];for(let r of a)if(r.reason==="device_absent"){let n=r.key.split("/")[0];t.set(n,(t.get(n)??0)+1)}else e.push(`${r.key}: ${o(s,`reason_${r.reason}`)}`);for(let[r,n]of t)e.push(o(s,"absent_circuit",{circuit:r,n}));return e}function Ye(a,s){let t=s?.values[a.index];if(t===void 0||t===""||t===me)return"";let e=a.writable?.options;if(e){let r=e.find(n=>n.name===t);return r?String(r.raw):""}return Number.isNaN(Number(t))?"":t}function ye(a){return a.read?!a.entity_id&&!a.passive?"not_listened":"waiting":"not_loaded"}function Je(a,s){let t=Math.max(0,Math.round(a));return t<90?o(s,"seconds_ago",{n:t}):t<90*60?o(s,"minutes_ago",{n:Math.round(t/60)}):t<36*3600?o(s,"hours_ago",{n:Math.round(t/3600)}):o(s,"days_ago",{n:Math.round(t/86400)})}function Ie(a,s){return new Intl.NumberFormat(s==="fr"?"fr-FR":"en-GB",{maximumFractionDigits:3,useGrouping:!1}).format(a).replace("-","\u2212")}function Xe(a,s,t){if(!a||a.min==null&&a.max==null)return"";let e=n=>n==null?"\u2026":Ie(n,t),r=`${e(a.min)} \u2026 ${e(a.max)}${s?` ${s}`:""}`;return a.step?`${r} (${Ie(a.step,t)})`:r}function Ge(a,s="en"){return a.values||a.writable?.options?"":Xe(a.range,a.unit,s)}var Qe=3,ge=15;function q(a){let s=a.trim();if(s===""||s==="-")return{ranges:[]};let t=[];for(let e of s.split(",")){let r=/^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$/.exec(e);if(!r)return{error:"day_format"};let[n,i,l,c]=r.slice(1).map(Number),u=n*60+i,_=l*60+c;if([i,c].some(p=>p%ge)||u>1440||_>1440||i>45||c>45)return{error:"day_quarter"};if(u>=_)return{error:"day_order"};t.push([u,_])}if(t.length>Qe)return{error:"day_too_many"};t.sort((e,r)=>e[0]-r[0]);for(let e=1;e<t.length;e++)if(t[e][0]<t[e-1][1])return{error:"day_overlap"};return{ranges:t}}function ze(a){let s=Math.floor(a/60),t=a%60;return`${String(s).padStart(2,"0")}:${String(t).padStart(2,"0")}`}function V(a){return a.length?a.map(([s,t])=>`${ze(s)}-${ze(t)}`).join(", "):"-"}function Ze(a,s,t){let e=c=>Math.round(Math.min(1,Math.max(0,c))*1440/ge)*ge,r=Math.min(e(s),e(t)),n=Math.max(e(s),e(t));n===r&&(n=Math.min(1440,r+60));let i=[];for(let[c,u]of a)c<=n&&u>=r?(r=Math.min(r,c),n=Math.max(n,u)):i.push([c,u]);let l=[...i,[r,n]].sort((c,u)=>c[0]-u[0]);return l.length>Qe?null:l}function Fe(a){let[s,t]=a.split(":").map(e=>Number(e));return s*60+(t||0)}function et(a){return a.map(([s,t])=>{let e=Fe(s),r=Fe(t);return{left:e/1440*100,width:Math.max(0,r-e)/1440*100,text:`${s}-${t}`}})}function B(a){let s=[],t=(e,r)=>{for(let n of a.filter(i=>i.parent===e))s.push([n,r]),t(n.id,r+1)};t("",0);for(let e of a)s.some(([r])=>r.id===e.id)||s.push([e,0]);return s}function $e(a,s,t){let e=[];for(let r of a.devices){let n=new Map(r.menus.map(u=>[u.id,u])),i=u=>{let _=[];for(let p=n.get(u);p;p=n.get(p.parent))_.unshift(f(p.label,t));return _.join(" \u203A ")},l=new Map(B(r.menus).map(([u],_)=>[u.id,_])),c=r.rows.filter(u=>u.kind==="setting").sort((u,_)=>(l.get(u.menu)??999)-(l.get(_.menu)??999));for(let u of c){let p=F(u,s)?.values[u.index],g;p===void 0?g=o(t,ye(u)):p===me?g=o(t,"not_available"):g=u.values&&f(u.values[p],t)||p;let m=u.values||u.writable?.options,v=u.writable?.minimum!=null?{min:u.writable.minimum,max:u.writable.maximum,step:u.writable.step}:u.range,b=u.writable?.options?u.writable.options.map(k=>f(k.label,t)).join(", "):u.values?Object.values(u.values).map(k=>f(k,t)).join(", "):"";e.push({device:f(r.label,t),menu:i(u.menu),label:f(u.label,t),value:g,unit:u.values?"":u.unit??"",range:m?b:Xe(v,null,t),writable:u.writable?o(t,u.writable.risk):o(t,"read_only")})}}return e}var ve=["device","menu","label","value","unit","range","writable"];function tt(a){return ve.map(s=>o(a,`col_${s}`))}function st(a,s){let t=s==="fr"?";":",",e=n=>n.includes(t)||/["\n\r]/.test(n)?`"${n.replace(/"/g,'""')}"`:n;return"\uFEFF"+[tt(s),...a.map(n=>ve.map(i=>n[i]))].map(n=>n.map(e).join(t)).join(`\r
`)+`\r
`}function D(a){return a.replace(/[&<>"']/g,s=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[s])}function rt(a,s,t){let e=[...new Set(a.map(l=>l.device))],r=ve.filter(l=>l!=="device"),n=tt(s).slice(1),i=e.map(l=>`<section><h2>${D(l)}</h2><table><thead><tr>${n.map(c=>`<th>${D(c)}</th>`).join("")}</tr></thead><tbody>${a.filter(c=>c.device===l).map(c=>`<tr>${r.map(u=>`<td>${D(c[u])}</td>`).join("")}</tr>`).join("")}</tbody></table></section>`);return`<!doctype html><html lang="${s}"><head><meta charset="utf-8"><title>${D(t.title)}</title>
<style>
@page{size:A4;margin:15mm 12mm}
body{font:10pt system-ui,sans-serif;margin:16px;color:#000;background:#fff}
h1{font-size:15pt;margin:0 0 4px}h2{font-size:12pt;margin:16px 0 6px}p{margin:0 0 8px;color:#333}
table{border-collapse:collapse;width:100%;table-layout:auto}
th,td{border:1px solid #999;padding:4px 7px;text-align:left;vertical-align:top;overflow-wrap:anywhere}
th{background:#eee}thead{display:table-header-group}tfoot{display:table-footer-group}
tr,td,th{break-inside:avoid;page-break-inside:avoid}
@media print{body{margin:0}h2{break-after:avoid;page-break-after:avoid}th{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
</style></head><body><h1>${D(t.title)}</h1><p>${D(t.subtitle)}</p>${i.join("")}
<p>${D(o(s,"report_no_factory"))}</p></body></html>`}function we(a,s){if(a.queued===0)return o(s,"read_nothing");let t=o(s,a.queued===1?"read_queued_one":"read_queued_n",{n:a.queued,s:a.seconds});if(a.ahead===0)return t;let e=a.wait>=90?Math.round(a.wait/60):0,r=e?o(s,"about_min",{n:e}):o(s,"about_s",{n:a.wait});return`${t} ${o(s,a.first_pass?"read_after_first_pass":"read_after_queue",{n:a.ahead,wait:r})}`}var K=class extends w{constructor(){super(),this.language="en",this.unread="",this.today=0,this.caption=""}render(){let s=this.language,t=E[s]??E.en;return d`<table>
      ${this.caption?d`<caption class="visually-hidden">${this.caption}</caption>`:h}
      <thead>
        <tr>
          <th scope="col"><span class="visually-hidden">${o(s,"programs")}</span></th>
          <td class="scale" aria-hidden="true">
            ${[0,6,12,18,24].map(e=>d`<span style="left:${e/24*100}%">${e}</span>`)}
          </td>
        </tr>
      </thead>
      <tbody>
        ${t.map((e,r)=>{let n=this.days?.[String(r+1)],i=n==null?this.unread||o(s,"day_unread"):n.length?n.map(([l,c])=>`${l}-${c}`).join(", "):o(s,"day_none");return d`<tr class=${this.today===r+1?"today":""}>
            <th scope="row">${e}</th>
            <td>
              <div class="day" aria-hidden="true">
                ${(n??[]).length?et(n).map(l=>d`<span class="bar" style="left:${l.left}%;width:${l.width}%"></span>`):h}
              </div>
              <div class="day-text">${i}</div>
            </td>
          </tr>`})}
      </tbody>
    </table>`}};K.properties={days:{attribute:!1},language:{type:String},unread:{type:String},today:{type:Number},caption:{type:String}},K.styles=j`
    :host {
      display: block;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th,
    td {
      text-align: start;
      vertical-align: top;
      padding: 6px 8px;
      border-bottom: 1px solid var(--divider-color);
    }
    tbody th {
      font-weight: 400;
      width: 8em;
    }
    tr.today th {
      font-weight: 500;
      color: var(--primary-color);
    }
    .scale {
      position: relative;
      height: 1.4em;
    }
    .scale span {
      position: absolute;
      transform: translateX(-50%);
      color: var(--secondary-text-color);
      font-size: 0.8em;
    }
    .day {
      position: relative;
      height: 14px;
      background: var(--secondary-background-color);
      border-radius: 4px;
    }
    .bar {
      position: absolute;
      top: 0;
      bottom: 0;
      background: var(--primary-color);
      border-radius: 4px;
    }
    .day-text {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }
    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      white-space: nowrap;
    }
  `;customElements.get("weishaupt-week-grid")||customElements.define("weishaupt-week-grid",K);var Z="__definitions__",ee="__faults__";function $t(a,s,t){let e=a.find(r=>r.id===s)?.parent??"";for(;e;){if(e===t)return!0;e=a.find(r=>r.id===e)?.parent??""}return!1}var vt="programs",Y=class extends w{constructor(){super();this._offset=0;this._readings={},this._programs={},this._available=!0,this._tick=0,this._queued={},this._reloading=!1,this._draft="",this._rowResult={},this._busy=!1,this._weekDraft={},this._weekResult={}}get _lang(){return Ve(this.hass?.language)}connectedCallback(){super.connectedCallback(),this._timer=window.setInterval(()=>this._tick+=1,3e4),this._entryId&&this._subscribe(this._entryId)}disconnectedCallback(){super.disconnectedCallback(),window.clearInterval(this._timer),this._unsubscribe?.(),this._unsubscribe=void 0}willUpdate(t){t.has("hass")&&this.hass&&this._installations===void 0&&!this._loading&&(this._loading="installations",this.hass.callWS({type:"weishaupt/panel/installations"}).then(e=>{this._installations=e,e.length&&this._select(e[0].entry_id)}).catch(e=>this._error=e.message))}async _select(t,e=!1){this._entryId=t,e||(this._tree=void 0,this._device=void 0,this._menu=void 0),this._readings={},this._programs={},this._queued={};try{let r=await this.hass.callWS({type:"weishaupt/panel/tree",entry_id:t});this._tree=r,this._loadFaults(0),r.devices.some(n=>n.id===this._device)||(this._device=r.devices[0]?.id,this._menu=r.devices[0]?.menus[0]?.id),await this._subscribe(t)}catch(r){if(e)throw r;this._error=r.message}}_loadFaults(t){window.clearTimeout(this._faultTimer),this._faultTimer=window.setTimeout(async()=>{if(this._entryId)try{this._faults=await this.hass.callWS({type:"weishaupt/panel/faults",entry_id:this._entryId})}catch{}},t)}async _readFaults(t){let e=await this.hass.callWS({type:"weishaupt/panel/read_faults",entry_id:this._entryId,device:t});this._queued={...this._queued,[`faults:${t}`]:e}}_report(){let t=this._tree,e=this._lang,r=$e(t,this._readings,e),n=new Date().toLocaleString(e==="fr"?"fr-FR":"en-GB"),i=rt(r,e,{title:o(e,"report_title"),subtitle:o(e,"report_subtitle",{date:n,version:t.definitions.version})}),l=window.open("","_blank");if(!l){this._rowResult={...this._rowResult,__report__:{text:o(e,"report_blocked"),error:!0}};return}l.document.open(),l.document.write(i),l.document.close(),l.focus(),l.print()}_csv(){let t=this._tree,e=this._lang,r=new Blob([st($e(t,this._readings,e),e)],{type:"text/csv;charset=utf-8"}),n=document.createElement("a");n.href=URL.createObjectURL(r),n.download=`weishaupt-settings-${new Date().toISOString().slice(0,10)}.csv`,n.click(),window.setTimeout(()=>URL.revokeObjectURL(n.href),1e3)}_faultsView(t){let e=this._lang,r=this._queued[`faults:${t.device}`],n=i=>i==null?"-":String(i);return d`<h2>${f(t.label,e)} — ${o(e,"faults")}</h2>
      ${t.not_listened?d`<p class="secondary">${o(e,"faults_unread",{n:t.not_listened})}</p>
            ${r!==void 0?d`<p class="secondary" role="status">${we(r,e)}</p>`:t.to_read===0||t.unread===0?d`<p class="secondary">${o(e,"faults_read_once")}</p>`:d`<p>
                    <button class="link" @click=${()=>this._readFaults(t.device)}>${o(e,"read_now")}</button>
                    <span class="secondary"
                      >${o(e,"read_cost",{n:t.to_read,s:Math.round(t.to_read*2.2)})}</span
                    >
                  </p>`}`:h}
      ${t.history?d`<h3>${o(e,"fault_history")}</h3>
            ${t.history.entries===null?d`<p class="secondary">${o(e,"day_unread")}</p>`:t.history.entries.length===0?d`<p class="secondary">${o(e,"fault_none")}</p>`:d`${t.history.ordered?h:d`<p class="secondary">${o(e,"fault_unordered")}</p>`}
                    <div class="scroll">
                      <table>
                        <thead>
                          <tr>
                            <th scope="col">${o(e,"fault_code")}</th>
                            <th scope="col">${o(e,"fault_text")}</th>
                            <th scope="col">${o(e,"fault_values")}</th>
                            <th scope="col">${o(e,"fault_slot")}</th>
                          </tr>
                        </thead>
                        <tbody>
                          ${t.history.entries.map(i=>d`<tr>
                              <th scope="row" class="nowrap">${i.code}</th>
                              <td>${f(i.text,e)||"-"}</td>
                              <td class="secondary">
                                ${i.values.map(l=>`${f(l.label,e)} ${l.value_labels?f(l.value_labels,e):l.value===null?"-":`${l.value}${l.unit?` ${l.unit}`:""}`}`).join(" \xB7 ")}
                              </td>
                              <td>${i.slot}</td>
                            </tr>`)}
                        </tbody>
                      </table>
                    </div>
                    <p class="secondary">${o(e,"fault_no_time")}</p>`}`:h}
      ${t.counters?d`<h3>${o(e,"fault_counters")}</h3>
            <div class="scroll">
              <table>
                <thead>
                  <tr>
                    <th scope="col">${o(e,"fault_number")}</th>
                    <th scope="col">${o(e,"fault_count")}</th>
                    <th scope="col">${o(e,"fault_text")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${t.counters.map(i=>d`<tr>
                      <th scope="row">${i.number}</th>
                      <td class=${i.count?"":"secondary"}>${i.count===null?o(e,"day_unread"):i.count}</td>
                      <td>${f(i.text,e)||"-"}</td>
                    </tr>`)}
                </tbody>
              </table>
            </div>`:h}
      ${t.log?d`<h3>${o(e,"fault_log")}</h3>
            <p>
              ${t.log.entry?o(e,"fault_log_fields",{id:n(t.log.entry.id),code:n(t.log.entry.code),type:n(t.log.entry.type),device:n(t.log.entry.device),time:n(t.log.entry.time)}):o(e,"day_unread")}
            </p>
            <p class="secondary">${o(e,"fault_log_hint")}</p>`:h}`}async _readProgram(t){if(!this._entryId)return;let e=await this.hass.callWS({type:"weishaupt/panel/read_program",entry_id:this._entryId,program:t});this._queued={...this._queued,[t]:e}}async _subscribe(t){this._unsubscribe?.(),this._unsubscribe=await this.hass.connection.subscribeMessage(e=>this._live(e),{type:"weishaupt/panel/subscribe",entry_id:t})}_live(t){if(this._offset=Date.now()/1e3-t.now,t.reloaded){this._unsubscribe=void 0,this._reloading=!0;let e=r=>{window.setTimeout(()=>{!this._entryId||!this.isConnected||this._select(this._entryId,!0).then(()=>this._reloading=!1,()=>r>0?e(r-1):this._error=o(this._lang,"reloading"))},2e3)};e(15);return}if(t.available!==void 0&&(this._available=t.available),t.readings){this._readings={...this._readings,...t.readings};let e=new Set((this._faults??[]).flatMap(r=>r.keys));Object.keys(t.readings).some(r=>e.has(r))&&this._loadFaults(1e3)}t.programs&&(this._programs={...this._programs,...t.programs})}_open(t){this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:t},bubbles:!0,composed:!0}))}_age(t){return Je(Date.now()/1e3-this._offset-t.when,this._lang)}render(){let t=this._lang;return this._error?d`<div class="message error" role="alert">${this._error}</div>`:this._installations===void 0?d`<div class="message">${o(t,"loading")}</div>`:this._installations.length?d`
      <header>
        <h1>${o(t,"title")}</h1>
        ${this._installations.length>1?d`<label
              >${o(t,"installation")}
              <select @change=${e=>this._select(e.target.value)}>
                ${this._installations.map(e=>d`<option value=${e.entry_id} ?selected=${e.entry_id===this._entryId}>${e.title}</option>`)}
              </select></label
            >`:h}
        ${this._clock()}
        ${this._tree?d`<button class="link" @click=${()=>this._report()}>${o(t,"report")}</button>
              <button class="link" @click=${()=>this._csv()}>${o(t,"export_csv")}</button>`:h}
        ${this._rowResult.__report__?d`<span class="error" role="alert">${this._rowResult.__report__.text}</span>`:h}
        ${this._tree?.writes?.clock_writable?d`<button class="link" ?disabled=${this._busy} @click=${()=>this._setClock()}>
              ${o(t,"set_clock")}
            </button>`:h}
        ${this._rowResult.__clock__?d`<span class=${this._rowResult.__clock__.error?"error":"secondary"} role="status"
              >${this._rowResult.__clock__.text}</span
            >`:h}
      </header>
      ${this._available?h:d`<div class="message warning" role="status">${o(t,"unavailable")}</div>`}
      ${this._reloading?d`<div class="message" role="status">${o(t,"reloading")}</div>`:h}
      ${this._tree?this._body(this._tree):d`<div class="message">${o(t,"loading")}</div>`}
      ${this._dialog?this._confirmDialog(this._dialog.answer):h}
    `:d`<div class="message">${o(t,"no_installation")}</div>`}async _call(t){this._busy=!0;try{let e=await this.hass.callWS({...t,entry_id:this._entryId,language:this._lang});return e.guard&&this._tree?.writes&&(this._tree={...this._tree,writes:{...this._tree.writes,...e.guard}}),e}catch(e){let r=e,n=!r?.code||r.code==="connection_lost"||/connection/i.test(r.message??"");return{status:"refused",code:n?"interrupted":r.code,message:n?o(this._lang,"interrupted"):r.message||r.code}}finally{this._busy=!1}}_switchOn(){let t=this._tree?.writes;if(!t)return!1;let e=t.switch_entity_id?this.hass.states[t.switch_entity_id]:void 0;return e?e.state==="on":t.switch}_resultText(t){let e=this._lang;return t.status==="refused"?{text:o(e,"not_written",{message:t.message??""}),error:!0}:t.kind==="clock"||t.requested!==void 0?{text:o(e,"clock_sent",{requested:t.requested??"",frame:t.frame??"",result:t.result_text??t.result??""}),error:t.result!=="sent"}:{text:o(e,"written_line",{before:t.before??"-",after:t.after??"",frame:t.frame?` (${t.frame})`:"",result:t.result_text??t.result??""}),error:t.result!=="ok"&&t.result!=="unchanged"}}_writing(t){this._rowResult={...this._rowResult,[t]:{text:o(this._lang,"writing"),error:!1}}}async _writeRow(t){let e=t.writable,r=Number(this._draft);this._writing(t.key);let n=await this._call({type:"weishaupt/panel/write",key:e.key,value:r});this._handle(n,t.key),n.status!=="refused"&&(this._editing=void 0)}_handle(t,e){if(t.status==="confirm"){this._dialog={answer:t,target:e};return}this._rowResult={...this._rowResult,[e]:this._resultText(t)}}async _setClock(){this._writing("__clock__"),this._handle(await this._call({type:"weishaupt/panel/clock"}),"__clock__")}async _confirmed(){let t=this._dialog;this._dialog=void 0,this._writing(t.target);let e=await this._call({type:"weishaupt/panel/confirm",pending_id:t.answer.pending_id});this._rowResult={...this._rowResult,[t.target]:this._resultText(e)}}async _withdrawn(){let t=this._dialog;this._dialog=void 0;let e={...this._rowResult};delete e[t.target],this._rowResult=e,await this._call({type:"weishaupt/panel/cancel",pending_id:t.answer.pending_id})}_confirmDialog(t){let e=this._lang,r=t.placeholders??{},n=t.kind==="clock";return d`<div class="backdrop">
      <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-title"
        @keydown=${i=>i.key==="Escape"&&this._withdrawn()}>
        <h2 id="confirm-title">${o(e,"confirm_title",{setting:r.setting??"",device:r.device??""})}</h2>
        ${n?d`<p>${o(e,"clock_current",{current:r.current??"-"})}</p>
              <p>${o(e,"clock_confirm",{send_at:r.send_at??"",late:r.late??""})}</p>`:d`<dl>
                <dt>${o(e,"current")}</dt>
                <dd>${r.current}</dd>
                <dt>${o(e,"new_value")}</dt>
                <dd><strong>${r.requested}</strong></dd>
                <dt>${o(e,"allowed")}</dt>
                <dd>${r.allowed}</dd>
              </dl>
              <p>${o(e,"path",r)}</p>
              <p class="secondary">${o(e,"regulation_note")}</p>`}
        <div class="actions">
          <button class="link" @click=${()=>this._withdrawn()}>${o(e,"cancel")}</button>
          <button class="primary" autofocus @click=${()=>this._confirmed()}>
            ${o(e,n?"confirm_clock":"confirm")}
          </button>
        </div>
      </div>
    </div>`}_writeCell(t){let e=this._lang,r=t.writable;if(!r)return d`<span class="secondary">${o(e,"read_only")}</span>`;let n=this._rowResult[t.key],i=d`<span class="badge ${r.risk}">${o(e,r.risk)}</span>${r.through?d`<div class="secondary">${o(e,"through",{circuit:r.through})}</div>`:h}`,l=h;return r.offered?this._editing===t.key?l=h:l=d`<button class="link" @click=${()=>this._startEdit(t)}>${o(e,"edit")}</button>`:l=d`<div class="secondary">
        ${r.why_not==="writes_disabled"?o(e,"not_offered_writes_disabled"):o(e,"not_offered",{reason:r.why_not??""})}
      </div>`,d`${i}${l}${n?d`<div class=${n.error?"error":"secondary"} role="status">${n.text}</div>`:h}`}_editForm(t){let e=this._lang,r=t.writable,n=F(t,this._readings);return d`<form
        class="edit"
        @submit=${i=>{i.preventDefault(),this._writeRow(t)}}
      >
        ${r.options?d`<select aria-label=${o(e,"new_value")}
              @change=${i=>this._draft=i.target.value}>
              <option value="" ?selected=${this._draft===""} disabled>…</option>
              ${r.options.map(i=>d`<option value=${i.raw} ?selected=${String(i.raw)===this._draft}>${f(i.label,e)}</option>`)}
            </select>`:d`<input type="number" aria-label=${o(e,"new_value")} .value=${this._draft}
              min=${r.minimum??""} max=${r.maximum??""} step=${r.step??"any"}
              @input=${i=>this._draft=i.target.value} />${t.unit?d` ${t.unit}`:h}`}
        <button class="primary" type="submit" ?disabled=${this._busy||this._draft===""}>${o(e,"write_now")}</button>
        <button class="link" type="button" @click=${()=>this._editing=void 0}>${o(e,"cancel")}</button>
        <div class="secondary">
          ${be(t,n,e)??"-"} ·
          ${o(e,"path_short",{address:r.address??"",register:r.register??"",source:r.source})}
        </div>
        <div class="secondary">${o(e,r.risk==="comfort"?"comfort_note":"regulation_note")}</div>
        ${this._tree?.writes&&!this._switchOn()?d`<div class="error">${o(e,"switch_off_hint")}</div>`:h}
      </form>`}_startEdit(t){this._draft=Ye(t,F(t,this._readings)),this._editing=t.key}_dayText(t,e){let r=t?.[e];return r==null?null:V(r.map(([n,i])=>[nt(n),nt(i)]))}_startWeek(t){let e=this._programs[t.key],r={};for(let n=1;n<=7;n++)r[String(n)]=this._dayText(e,String(n))??"";this._weekDraft={...this._weekDraft,[t.key]:r},this._weekResult={...this._weekResult,[t.key]:void 0}}_setDay(t,e,r){this._weekDraft={...this._weekDraft,[t]:{...this._weekDraft[t],[e]:r}}}_changed(t){let e=this._weekDraft[t.key]??{},r=this._programs[t.key];return Object.keys(e).filter(n=>{let i=this._dayText(r,n);if(i===null&&e[n].trim()==="")return!1;let l=q(e[n]);return("ranges"in l?V(l.ranges):e[n])!==i})}async _writeWeek(t){let e=this._weekDraft[t.key],r={};for(let _ of this._changed(t))r[_]=e[_];this._weekResult={...this._weekResult,[t.key]:{text:o(this._lang,"writing"),error:!1}};let n=await this._call({type:"weishaupt/panel/write_days",program:t.key,days:r}),i=this._lang;if(n.status==="refused"){this._weekResult={...this._weekResult,[t.key]:this._resultText(n)};return}let l=E[i]??E.en,c=Object.entries(n.days??{}).map(([_,p])=>o(i,"written_line",{before:`${l[Number(_)-1]} ${p.before??"-"}`,after:p.after??"",frame:p.frames?.length?` (${p.frames.join(", ")})`:"",result:p.result_text??p.result??""}));this._weekResult={...this._weekResult,[t.key]:{text:c.join(" \xB7 "),error:!1}};let u={...this._weekDraft};delete u[t.key],this._weekDraft=u}_copy(t,e,r){let n=this._weekDraft[t][e],i=r==="all"?["1","2","3","4","5","6","7"]:r==="weekdays"?["1","2","3","4","5"]:r==="weekend"?["6","7"]:[r],l={...this._weekDraft[t]};for(let c of i)c!==e&&(l[c]=n);this._weekDraft={...this._weekDraft,[t]:l}}_dragStart(t,e,r){let n=t.currentTarget;if(t.target.classList.contains("bar"))return;let i=n.getBoundingClientRect();this._drag={program:e,day:r,from:(t.clientX-i.left)/i.width,element:n},n.setPointerCapture(t.pointerId)}_dragEnd(t){let e=this._drag;if(this._drag=void 0,!e)return;let r=e.element.getBoundingClientRect(),n=q(this._weekDraft[e.program][e.day]);if(!("ranges"in n))return;let i=Ze(n.ranges,e.from,(t.clientX-r.left)/r.width);i&&this._setDay(e.program,e.day,V(i))}_removeRange(t,e,r){let n=q(this._weekDraft[t][e]);"ranges"in n&&this._setDay(t,e,V(n.ranges.filter((i,l)=>l!==r)))}_clock(){let t=this._tree?.clock.entity_id,e=t?this.hass.states[t]:void 0;if(!t||!e||Number.isNaN(Number(e.state)))return h;let r=this._lang,n=Math.round(Number(e.state)),i=n===0?o(r,"clock_on_time"):o(r,n>0?"clock_ahead":"clock_behind",{n:Math.abs(n)});return d`<button class="clock link" @click=${()=>this._open(t)}>
      ${o(r,"clock_line",{label:o(r,"clock_offset"),text:i})}
    </button>`}_body(t){let e=t.devices.find(r=>r.id===this._device);return d`<div class=${this.narrow?"layout narrow":"layout"}>
      <nav aria-label=${o(this._lang,"devices")}>${this._nav(t)}</nav>
      <main>
        ${this._menu===Z?this._definitions(t):this._menu===ee?(()=>{let r=this._faults?.find(n=>n.device===this._device);return r?this._faultsView(r):d`<p class="secondary">${o(this._lang,"loading")}</p>`})():e?this._device_view(e):h}
      </main>
    </div>`}_nav(t){let e=this._lang;if(this.narrow){let n=`${this._device??""}|${this._menu??""}`;return d`<label class="choose"
        >${o(e,"devices")}
        <select
          @change=${i=>{let[l,c]=i.target.value.split("|");this._device=l,this._menu=c}}
        >
          ${t.devices.map(i=>d`<optgroup label=${f(i.label,e)}>
              ${B(i.menus).map(([l,c])=>d`<option value=${`${i.id}|${l.id}`} ?selected=${n===`${i.id}|${l.id}`}>
                    ${"\xA0\xA0".repeat(c)}${f(l.label,e)}
                  </option>`)}
              ${this._faults?.some(l=>l.device===i.id)?d`<option value=${`${i.id}|${ee}`} ?selected=${n===`${i.id}|${ee}`}>
                    ${o(e,"faults")}
                  </option>`:h}
            </optgroup>`)}
          <option value=${`${this._device??""}|${Z}`} ?selected=${this._menu===Z}>
            ${o(e,"definitions")}
          </option>
        </select></label
      >`}let r=(n,i,l,c)=>{let u=this._device===n&&this._menu===i;return d`<li>
        <button
          class="menu depth${c}"
          aria-current=${u?"page":"false"}
          @click=${()=>{this._device=n,this._menu=i}}
        >
          ${l}
        </button>
      </li>`};return d`<ul>
      ${t.devices.map(n=>d`<li>
          <span class="device">${f(n.label,e)}</span>
          <ul>
            ${B(n.menus).map(([i,l])=>r(n.id,i.id,f(i.label,e),l))}
            ${this._faults?.some(i=>i.device===n.id)?r(n.id,ee,o(e,"faults"),0):h}
          </ul>
        </li>`)}
      ${r(this._device??"",Z,o(e,"definitions"),0)}
    </ul>`}_device_view(t){let e=this._lang,r=t.menus.find(l=>l.id===this._menu),n=[t.addresses.length?`${o(e,"address")} ${t.addresses.join(", ")}`:"",t.software?`${o(e,"software")} ${t.software}`:"",t.hardware?`${o(e,"hardware")} ${t.hardware}`:""].filter(Boolean),i=B(t.menus).filter(([l])=>l.id===this._menu||$t(t.menus,l.id,this._menu??"")).map(([l])=>[l,t.rows.filter(c=>c.menu===l.id)]).filter(([,l])=>l.length);return d`<h2>${f(t.label,e)}${r?d` — ${f(r.label,e)}`:h}</h2>
      ${n.length?d`<p class="secondary">${n.join(" \xB7 ")}</p>`:h}
      ${this._menu===vt?this._programs_view(t):h}
      ${i.length?d`<p class="secondary">${o(e,"write_hint")}</p>`:h}
      ${i.map(([l,c])=>d`${l.id!==this._menu?d`<h3>${f(l.label,e)}</h3>`:h}${this._table(c)}`)}`}_table(t){let e=this._lang;return this._tick,d`<div class="scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">${o(e,"name")}</th>
              <th scope="col">${o(e,"value")}</th>
              <th scope="col">${o(e,"age")}</th>
              <th scope="col">${o(e,"range")}</th>
              <th scope="col">${o(e,"write")}</th>
              <th scope="col">${o(e,"entity")}</th>
            </tr>
          </thead>
          <tbody>
            ${t.map(r=>{let n=F(r,this._readings),i=be(r,n,e),l=Be(f(r.description,e),f(r.label,e))?"":f(r.description,e);return d`<tr>
                <th scope="row">
                  ${f(r.label,e)}
                  ${l?d`<div class="description">${l}</div>`:h}
                </th>
                <td class="nowrap">${i??d`<span class="secondary">${o(e,ye(r))}</span>`}</td>
                <td class="secondary nowrap">
                  ${n?this._age(n):""}${n?.kept?d`<div class="kept">${o(e,"kept")}</div>`:h}${r.passive?d`<div>${o(e,"passive")}</div>`:h}
                </td>
                <td class="nowrap">${Ge(r,e)}</td>
                <td>${this._writeCell(r)}</td>
                <td>
                  ${r.entity_id?d`<button class="link" @click=${()=>this._open(r.entity_id)}>${o(e,"open")}</button>`:h}
                </td>
              </tr>${this._editing===r.key?d`<tr class="edit-row"><td colspan="6">${this._editForm(r)}</td></tr>`:h}`})}
          </tbody>
        </table>
      </div>`}_programs_view(t){let e=this._lang,r=E[e]??E.en,n=this._tree?.writes;return d`${t.programs.map(i=>{let l=this._programs[i.key],c=this._weekDraft[i.key],u=c!==void 0,_=u?this._changed(i):[],p=u?Object.fromEntries(Object.entries(c).map(([b,k])=>{let y=q(k);return[b,"error"in y?y.error:null]})):{},g=Object.values(p).some(Boolean),m=i.read?i.listened?i.writable?o(e,"editable"):o(e,"not_editable"):o(e,"program_not_listened"):o(e,"not_read_program"),v=this._weekResult[i.key];return d`<section class="program">
        <h3>
          ${f(i.label,e)}
          ${i.entity_id?d`<button class="link" @click=${()=>this._open(i.entity_id)}>${o(e,"open")}</button>`:h}
          ${i.writable&&n&&!u?d`<button class="link" @click=${()=>this._startWeek(i)}>${o(e,"edit_days")}</button>`:h}
        </h3>
        <p class="secondary">${m}</p>
        ${i.read&&!i.listened?this._queued[i.key]!==void 0?d`<p class="secondary" role="status">${we(this._queued[i.key],e)}</p>`:d`<p>
                <button class="link" @click=${()=>this._readProgram(i.key)}>${o(e,"read_now")}</button>
                <span class="secondary"
                  >${o(e,"read_cost",{n:i.to_read,s:Math.round(i.to_read*2.2)})}</span
                >
              </p>`:h}
        ${u?d`<p class="secondary">${o(e,"drag_hint")}</p>`:h}
        ${u?d`<table class="week">
          <caption class="visually-hidden">${f(i.label,e)}</caption>
          <thead>
            <tr>
              <th scope="col"><span class="visually-hidden">${o(e,"programs")}</span></th>
              <td class="scale" aria-hidden="true">
                ${[0,6,12,18,24].map(b=>d`<span style="left:${b/24*100}%">${b}</span>`)}
              </td>
            </tr>
          </thead>
          <tbody>
            ${r.map((b,k)=>{let y=String(k+1);if(u){let xe=q(c[y]),it="ranges"in xe?xe.ranges:[],te=p[y];return d`<tr class=${_.includes(y)?"changed":""}>
                  <th scope="row">${b}</th>
                  <td>
                    <div
                      class="day editable"
                      aria-hidden="true"
                      @pointerdown=${$=>this._dragStart($,i.key,y)}
                      @pointerup=${$=>this._dragEnd($)}
                    >
                      ${it.map(([$,A],at)=>d`<span
                          class="bar"
                          style="left:${$/1440*100}%;width:${(A-$)/1440*100}%"
                          @click=${()=>this._removeRange(i.key,y,at)}
                        ></span>`)}
                    </div>
                    <div class="day-edit">
                      <input
                        type="text"
                        aria-label=${b}
                        aria-invalid=${te?"true":"false"}
                        placeholder=${l?.[y]==null?o(e,"day_unread"):""}
                        .value=${c[y]}
                        @input=${$=>this._setDay(i.key,y,$.target.value)}
                      />
                      <label class="secondary"
                        >${o(e,"copy_to")}
                        <select
                          @change=${$=>{let A=$.target;A.value&&this._copy(i.key,y,A.value),A.value=""}}
                        >
                          <option value="">…</option>
                          <option value="all">${e==="fr"?"tous les jours":"every day"}</option>
                          <option value="weekdays">${e==="fr"?"lundi \u2013 vendredi":"Monday \u2013 Friday"}</option>
                          <option value="weekend">${e==="fr"?"samedi, dimanche":"Saturday, Sunday"}</option>
                          ${r.map(($,A)=>A===k?h:d`<option value=${String(A+1)}>${$}</option>`)}
                        </select></label
                      >
                    </div>
                    ${te?d`<div class="error" role="alert">${o(e,te)}</div>`:h}
                  </td>
                </tr>`}return h})}
          </tbody>
        </table>`:d`<weishaupt-week-grid
              .days=${l}
              language=${e}
              unread=${o(e,i.listened?"day_unread":"not_listened")}
              caption=${f(i.label,e)}
            ></weishaupt-week-grid>`}
        ${u&&n?d`<p class="secondary">
                ${o(e,_.length===1?"cost_one":"cost",{days:_.length,writes:_.length*3,used:n.writes_last_hour,max:n.max_per_hour})}
              </p>
              ${this._switchOn()?h:d`<p class="error">${o(e,"switch_off_hint")}</p>`}
              <div class="actions">
                <button class="link" @click=${()=>{let b={...this._weekDraft};delete b[i.key],this._weekDraft=b}}>${o(e,"discard")}</button>
                <button class="primary" ?disabled=${this._busy||g||!_.length}
                  @click=${()=>this._writeWeek(i)}>${o(e,"write_days")}</button>
              </div>`:h}
        ${v?d`<p class=${v.error?"error":"secondary"} role="status">${v.text}</p>`:h}
      </section>`})}`}_definitions(t){let e=this._lang,r=t.definitions,n=l=>l.length?d`<ul>${l.map(c=>d`<li><code>${c}</code></li>`)}</ul>`:d`${o(e,"none")}`,i=t.writes;return d`<h2>${o(e,"definitions")}</h2>
      <dl>
        <dt>${o(e,"in_use")}</dt>
        <dd>
          ${r.version}${r.commit?d` <code>${r.commit.slice(0,7)}</code>`:h} —
          ${r.source==="bundled"?o(e,"source_bundled"):o(e,"source_file",{file:r.source})}
        </dd>
        <dt>${o(e,"messages")}</dt>
        <dd>
          ${o(e,"readable",{usable:r.usable,readable:r.usable+r.not_usable.filter(l=>l.reason==="mismatch"||l.reason==="other").length})}
        </dd>
        <dt>${o(e,"not_usable")}</dt>
        <dd>${n(Ke(r.not_usable,e))}</dd>
        <dt>${o(e,"refused")}</dt>
        <dd>${n(Object.entries(r.refused).map(([l,c])=>`${l}: ${c}`))}</dd>
        <dt>${o(e,"mismatches")}</dt>
        <dd>${n(r.mismatches.map(l=>`${l.key}: ${l.reason}${l.detail?` (${l.detail})`:""}`))}</dd>
        <dt>${o(e,"named_from_metadata")}</dt>
        <dd>
          ${n(r.named_from_metadata.map(l=>l.disabled?`${l.entity_id} (${o(e,"disabled")})`:l.entity_id))}
        </dd>
        <dt>${o(e,"not_named")}</dt>
        <dd>${n(r.not_named)}</dd>
        <dt>${o(e,"ebusd")}</dt>
        <dd>${t.ebusd.version??"?"}${t.ebusd.own_address?` (${t.ebusd.own_address})`:""}</dd>
        <dt>${o(e,"unknown_addresses")}</dt>
        <dd>${n(t.unknown_addresses)}</dd>
        <dt>${o(e,"writes")}</dt>
        <dd>
          ${i?d`${o(e,this._switchOn()?"switch_on":"switch_off")} ·
              ${o(e,"capability",{value:i.capability})} ·
              ${o(e,"per_hour",{n:i.writes_last_hour,max:i.max_per_hour})}`:o(e,"writes_off")}
        </dd>
        ${i?d`<dt>${o(e,"read_only_settings")}</dt>
              <dd>${n(i.read_only.map(l=>`${l.key}: ${l.reason}`))}</dd>`:h}
      </dl>`}};Y.properties={hass:{attribute:!1},narrow:{type:Boolean},_installations:{state:!0},_entryId:{state:!0},_tree:{state:!0},_readings:{state:!0},_programs:{state:!0},_available:{state:!0},_device:{state:!0},_menu:{state:!0},_error:{state:!0},_tick:{state:!0},_queued:{state:!0},_reloading:{state:!0},_editing:{state:!0},_draft:{state:!0},_rowResult:{state:!0},_busy:{state:!0},_dialog:{state:!0},_weekDraft:{state:!0},_weekResult:{state:!0},_faults:{state:!0}},Y.styles=j`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
      font-family: var(--paper-font-body1_-_font-family, inherit);
    }
    header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 12px 24px;
      padding: 12px 16px;
      background: var(--app-header-background-color, var(--card-background-color));
      color: var(--app-header-text-color, var(--primary-text-color));
      border-bottom: 1px solid var(--divider-color);
    }
    h1 {
      font-size: 20px;
      font-weight: 400;
      margin: 0;
    }
    h2 {
      font-size: 18px;
      font-weight: 500;
      margin: 0 0 8px;
    }
    h3 {
      font-size: 16px;
      font-weight: 500;
      margin: 16px 0 4px;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(200px, 260px) 1fr;
      gap: 16px;
      padding: 16px;
    }
    .layout.narrow {
      grid-template-columns: 1fr;
    }
    nav,
    main {
      background: var(--card-background-color);
      border-radius: var(--ha-card-border-radius, 12px);
      border: 1px solid var(--divider-color);
      padding: 12px;
      min-width: 0;
    }
    nav ul {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    label.choose {
      display: flex;
      flex-direction: column;
      gap: 4px;
      color: var(--secondary-text-color);
    }
    select {
      font: inherit;
      padding: 6px;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 6px;
    }
    .device {
      display: block;
      font-weight: 500;
      margin: 12px 0 4px;
    }
    button {
      font: inherit;
      color: inherit;
    }
    button.menu {
      display: block;
      width: 100%;
      text-align: start;
      border: 0;
      background: none;
      padding: 6px 8px;
      border-radius: 6px;
      cursor: pointer;
    }
    button.menu.depth1 {
      padding-inline-start: 24px;
    }
    button.menu.depth2 {
      padding-inline-start: 40px;
    }
    button.menu[aria-current="page"] {
      background: var(--secondary-background-color);
      color: var(--primary-color);
      font-weight: 500;
    }
    button:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
    }
    button.link {
      border: 1px solid var(--divider-color);
      background: none;
      border-radius: 6px;
      padding: 2px 8px;
      cursor: pointer;
      color: var(--primary-color);
    }
    .nowrap {
      white-space: nowrap;
    }
    .scroll {
      overflow-x: auto;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th,
    td {
      text-align: start;
      vertical-align: top;
      padding: 6px 8px;
      border-bottom: 1px solid var(--divider-color);
    }
    thead th {
      font-weight: 500;
      color: var(--secondary-text-color);
    }
    tbody th {
      font-weight: 400;
      min-width: 12em;
    }
    .description,
    .secondary {
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }
    .kept {
      font-style: italic;
    }
    .badge {
      white-space: nowrap;
      border-radius: 10px;
      padding: 1px 8px;
      border: 1px solid currentColor;
    }
    .badge.comfort {
      color: var(--success-color, var(--primary-color));
    }
    .badge.regulation {
      color: var(--warning-color, var(--primary-color));
    }
    .message {
      padding: 16px;
    }
    .message.error {
      color: var(--error-color);
    }
    .message.warning {
      color: var(--warning-color);
    }
    table.week th {
      width: 8em;
    }
    .scale {
      position: relative;
      height: 1.4em;
    }
    .scale span {
      position: absolute;
      transform: translateX(-50%);
      color: var(--secondary-text-color);
      font-size: 0.8em;
    }
    .day {
      position: relative;
      height: 14px;
      background: var(--secondary-background-color);
      border-radius: 4px;
    }
    .bar {
      position: absolute;
      top: 0;
      bottom: 0;
      background: var(--primary-color);
      border-radius: 4px;
    }
    .day-text {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }
    dl {
      display: grid;
      grid-template-columns: minmax(0, max-content) minmax(0, 1fr);
      gap: 6px 16px;
    }
    dt {
      color: var(--secondary-text-color);
    }
    dd {
      margin: 0;
      min-width: 0; /* a long entity id wraps inside its column instead of widening the page */
      overflow-wrap: anywhere;
    }
    code {
      overflow-wrap: anywhere;
    }
    dd ul {
      margin: 0;
      padding-inline-start: 16px;
    }
    .error {
      color: var(--error-color);
    }
    button.primary {
      border: 0;
      border-radius: 6px;
      padding: 4px 12px;
      cursor: pointer;
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }
    button:disabled {
      opacity: 0.5;
      cursor: default;
    }
    form.edit {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 4px 8px;
      margin-top: 6px;
    }
    form.edit div {
      flex-basis: 100%;
    }
    input {
      font: inherit;
      padding: 4px 6px;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 6px;
    }
    input[type="number"] {
      width: 6em;
    }
    input[aria-invalid="true"] {
      border-color: var(--error-color);
    }
    .day.editable {
      cursor: crosshair;
      height: 22px;
      touch-action: none;
    }
    .day.editable .bar {
      cursor: pointer;
    }
    .day-edit {
      display: flex;
      flex-wrap: wrap;
      gap: 4px 12px;
      margin-top: 4px;
      align-items: center;
    }
    .day-edit input {
      flex: 1 1 14em;
      min-width: 0;
    }
    tr.changed th {
      font-weight: 500;
      color: var(--primary-color);
    }
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 8px;
    }
    .backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
      z-index: 10;
    }
    .dialog {
      background: var(--card-background-color);
      color: var(--primary-text-color);
      border-radius: var(--ha-card-border-radius, 12px);
      padding: 16px 20px;
      max-width: 560px;
      width: 100%;
      max-height: 90vh;
      overflow: auto;
    }
    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      white-space: nowrap;
    }
    @media (max-width: 600px) {
      dl {
        grid-template-columns: 1fr;
      }
    }
  `;customElements.get("weishaupt-panel")||customElements.define("weishaupt-panel",Y);function nt(a){let[s,t]=a.split(":").map(Number);return s*60+(t||0)}export{Y as WeishauptPanel};
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/lit-html.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
